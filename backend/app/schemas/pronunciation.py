"""Pronunciation evaluation contract."""
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


EvaluationText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PronunciationScore = Annotated[int, Field(strict=True, ge=0, le=100)]


class PronunciationEvaluation(BaseModel):
    score: PronunciationScore
    feedback: EvaluationText
    tip: EvaluationText


class HeardPronunciation(BaseModel):
    """Phones heard by Gemini before the backend checks the target."""

    phones: Annotated[list[str], Field(max_length=160)] | None
