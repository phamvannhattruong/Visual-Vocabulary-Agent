"""AI response parsing and chat message normalization utilities."""
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException

from backend.app.schemas.chat import ChatRequest


def extract_json_from_ai(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse first JSON object enclosed in curly braces from AI response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group().strip())
        except Exception:
            return None
    return None


def extract_quiz(text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Extract multiple-choice quiz JSON enclosed within [QUIZ_START] and [QUIZ_END] tags.
    Returns cleaned text and parsed quiz dict.
    """
    quiz_match = re.search(r"\[QUIZ_START\](.*?)\[QUIZ_END\]", text, re.DOTALL)
    if quiz_match:
        try:
            quiz_data = json.loads(quiz_match.group(1).strip())
            clean_text = re.sub(r"\[QUIZ_START\].*?\[QUIZ_END\]", "", text, flags=re.DOTALL).strip()
            return clean_text, quiz_data
        except Exception:
            return text, None
    return text, None


def build_message_list(request: ChatRequest) -> List[Dict[str, str]]:
    """Support extracting message list from standard ChatRequest payload."""
    if hasattr(request, "messages") and request.messages:
        return [{"role": m.get("role") if isinstance(m, dict) else m.role,
                 "content": m.get("content") if isinstance(m, dict) else m.content}
                for m in request.messages]
    elif hasattr(request, "message") and getattr(request, "message", None):
        return [{"role": "user", "content": request.message.strip()}]
    else:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp nội dung tin nhắn.")

