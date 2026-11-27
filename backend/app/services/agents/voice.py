import io

from gtts import gTTS

from backend.app.schemas.pronunciation import HeardPronunciation, PronunciationEvaluation
from backend.app.services.agents.base import Agent
from backend.app.utils.pronunciation import PHONE_IPA, grade_pronunciation, reference_pronunciations


class VoiceAgent(Agent):
    def __init__(self, default_language: str = 'en'):
        # Gọi hàm khởi tạo của lớp cha Agent để kế thừa cấu hình (Native Client & LangChain)
        super().__init__()
        self.default_language = default_language

    def convert_text_to_speech(self, text: str, language: str = 'en'):
        if not text:
            return None
        try:
            tts = gTTS(text=text, lang=language, slow=True)
            audio_stream = io.BytesIO()
            tts.write_to_fp(audio_stream)
            return audio_stream.getvalue()
        except Exception as e:
            print(f"Error in Voice Agent TTS: {e}")
            return None

    def create_vocabulary_audio(self, vocab_list: list):
        combined_text = ", ".join(vocab_list)
        return self.convert_text_to_speech(combined_text, language=self.default_language)

    def create_lesson_audio(self, lesson_md: str):
        combined_text = lesson_md.replace("#", "").replace("*", "").replace("-", "").strip()
        return self.convert_text_to_speech(combined_text, language=self.default_language)

    def check_speech(self, target_word: str, audio_bytes: bytes) -> PronunciationEvaluation:
        """Evaluate a decoded WAV recording against the target word."""
        references = reference_pronunciations(target_word)
        phone_labels = ", ".join(f"{phone}=/{ipa}/" for phone, ipa in PHONE_IPA.items())
        prompt = f"""
        Listen to this short recording of a learner practicing spoken English.
        Return the speech sounds actually heard, in order, as a list of the phone codes below.
        Use broad phone categories, ignoring stress, release, and other allophonic differences.
        Include clear substituted and extra phones. Leave out phones that were not produced.
        Do not correct the speech to a likely English word or infer its spelling.
        Return null for phones if there is no speech or noise makes the sequence unreliable.
        Phone codes: {phone_labels}.
        """

        response_text = self.generate_response(
            contents=[prompt, {"mime_type": "audio/wav", "data": audio_bytes}],
            config={
                "response_mime_type": "application/json",
                "response_schema": HeardPronunciation,
                "http_options": {"timeout": 10000},
            },
        )
        observed = HeardPronunciation.model_validate_json(response_text)
        return grade_pronunciation(references, observed.phones)
