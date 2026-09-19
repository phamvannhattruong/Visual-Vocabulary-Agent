"""Conversational tutor API endpoints."""
import json
from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

if TYPE_CHECKING:
    from backend.app.services.agents.chat import ChatAgent

SYSTEM_PROMPT = (
    "You are an English-learning tutor. Answer only questions about English "
    "vocabulary, grammar, translation, or pronunciation. Politely redirect "
    "unrelated questions in Vietnamese."
)


@lru_cache
def get_chat_agent() -> "ChatAgent":
    from backend.app.services.agents.chat import ChatAgent

    return ChatAgent(
        repo_id="DeeplearningVN/Chatbot_English",
        filename="meta-llama-3.1-8b.Q4_K_M.gguf",
        system_prompt=SYSTEM_PROMPT,
        n_ctx=2048,
        n_gpu_layers=10,
    )


def with_system_prompt(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Use one trusted tutor instruction for every request."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *(message for message in messages if message.get("role") != "system"),
    ]


@router.post("/chat-bot", response_model=ChatResponse)
@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        reply = get_chat_agent().generate_response(with_system_prompt(request.messages))
        return ChatResponse(reply=reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot failed to generate response: {exc}") from exc


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    try:
        def event_stream():
            for chunk in get_chat_agent().stream_response(with_system_prompt(request.messages)):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Streaming failed: {exc}") from exc
