"""Compare heard phones with US English pronunciation variants from CMUdict."""

import gzip
import re
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from backend.app.schemas.pronunciation import PronunciationEvaluation
from backend.app.utils.audio import InvalidRecording


# CMUdict: https://github.com/cmusphinx/cmudict/tree/74790861f652b15e4ac49015a90074ad62a27690
_DICTIONARY = Path(__file__).resolve().parents[2] / "resources" / "pronunciation" / "cmudict.dict.gz"

PHONE_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AX": "ə",
    "AY": "aɪ", "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ",
    "ER": "ɝ", "EY": "eɪ", "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ",
    "IY": "i", "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n",
    "NG": "ŋ", "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "ɹ", "S": "s",
    "SH": "ʃ", "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v",
    "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}

MAX_SCORE_WITH_SOUND_ERROR = 74

PhoneSequence = tuple[str, ...]
PronunciationVariants = tuple[PhoneSequence, ...]


def _normalize_phone(value: str) -> str:
    phone = value.strip().upper()
    if phone == "AH0":
        return "AX"
    return re.sub(r"[012]$", "", phone)


@lru_cache(maxsize=1)
def _pronunciation_dictionary() -> dict[str, list[PhoneSequence]]:
    dictionary: dict[str, list[PhoneSequence]] = {}
    with gzip.open(_DICTIONARY, mode="rt", encoding="utf-8") as source:
        for line in source:
            entry = line.split("#", 1)[0].split()
            if len(entry) < 2 or entry[0].startswith(";;;"):
                continue
            word = entry[0].split("(", 1)[0].casefold()
            phones = tuple(_normalize_phone(phone) for phone in entry[1:])
            variants = dictionary.setdefault(word, [])
            if phones and phones not in variants:
                variants.append(phones)
    return dictionary


def reference_pronunciations(target: str) -> list[PronunciationVariants]:
    normalized = target.casefold().replace("’", "'").strip(" \t\n.,!?")
    dictionary = _pronunciation_dictionary()
    words = [normalized] if normalized in dictionary else re.split(r"[\s-]+", normalized)
    references = [tuple(dictionary.get(word, ())) for word in words]
    if not all(references):
        raise InvalidRecording("Chưa có phiên âm tham chiếu cho từ này. Hãy chọn từ khác để luyện.")
    return references


class _Alignment(NamedTuple):
    errors: int = 0
    reference_length: int = 0
    first_difference: tuple[str | None, str | None] | None = None

    def compare(self, expected: str | None, heard: str | None) -> "_Alignment":
        differs = expected != heard
        difference = self.first_difference or ((expected, heard) if differs else None)
        return _Alignment(self.errors + differs, self.reference_length + (expected is not None), difference)

    def rank(self) -> tuple[int, int]:
        return self.errors, -self.reference_length


def _best_alignment(references: list[PronunciationVariants], heard: PhoneSequence) -> _Alignment:
    # Each cell represents the best alignment for one prefix of the heard phones.
    previous = [_Alignment()]
    for phone in heard:
        previous.append(previous[-1].compare(None, phone))

    for variants in references:
        variant_rows = []
        for variant in variants:
            row = previous
            for expected in variant:
                next_row = [row[0].compare(expected, None)]
                for i, observed in enumerate(heard):
                    choices = (
                        row[i].compare(expected, observed),
                        row[i + 1].compare(expected, None),
                        next_row[i].compare(None, observed),
                    )
                    next_row.append(min(choices, key=_Alignment.rank))
                row = next_row
            variant_rows.append(row)
        previous = [min(cells, key=_Alignment.rank) for cells in zip(*variant_rows)]
    return previous[-1]


def grade_pronunciation(references: list[PronunciationVariants], observed: list[str] | None) -> PronunciationEvaluation:
    if not observed:
        raise InvalidRecording("Không nghe rõ các âm trong bản ghi. Hãy thu âm lại.")

    heard = tuple(_normalize_phone(phone) for phone in observed)
    if any(phone not in PHONE_IPA for phone in heard):
        raise ValueError("The model returned an unknown phone.")

    alignment = _best_alignment(references, heard)
    if alignment.first_difference is None:
        return PronunciationEvaluation(
            score=100,
            feedback="Các âm nghe được khớp với một cách phát âm tham chiếu.",
            tip="Tiếp tục luyện và nghe lại âm mẫu nếu cần.",
        )

    expected, actual = alignment.first_difference
    if expected is None:
        feedback = f"Nghe thấy âm thừa /{PHONE_IPA[actual]}/."
    elif actual is None:
        feedback = f"Chưa nghe thấy âm /{PHONE_IPA[expected]}/."
    else:
        feedback = f"Nghe thấy âm gần /{PHONE_IPA[actual]}/ ở chỗ cần âm /{PHONE_IPA[expected]}/."
    length = max(len(heard), alignment.reference_length)
    score = min(round(100 * (1 - alignment.errors / length)), MAX_SCORE_WITH_SOUND_ERROR)
    return PronunciationEvaluation(
        score=score,
        feedback=feedback,
        tip="Nghe mẫu, tập riêng âm vừa được chỉ ra rồi thu âm lại cả từ.",
    )
