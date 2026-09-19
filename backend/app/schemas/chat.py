"""Conversation request and response contracts."""
from typing import Dict, List

from pydantic import BaseModel


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]


class ChatResponse(BaseModel):
    reply: str
