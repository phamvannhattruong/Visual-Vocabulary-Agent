"""Pronunciation evaluation contract."""
from pydantic import BaseModel, Field


class PronunciationEvaluation(BaseModel):
    score: int = Field(..., description="Pronunciation score from 0 to 100")
    feedback: str = Field(..., description="Vietnamese pronunciation feedback")
    tip: str = Field(..., description="Vietnamese improvement suggestion")
