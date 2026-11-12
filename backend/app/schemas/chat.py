"""Conversation request and response contracts."""
from typing import Dict, List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    session_id: Optional[str] = None
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
