from pydantic import BaseModel, Field
from typing import List, Optional

class PronunciationEvaluation(BaseModel):
    score: int = Field(..., description="Điểm số phát âm từ 0 đến 100")
    feedback: str = Field(..., description="Nhận xét chi tiết bằng tiếng Việt (ví dụ: Thiếu âm cuối 's', Phát âm sai nguyên âm 'a')")
    tip: str = Field(..., description="Mẹo cải thiện phát âm bằng tiếng Việt")
