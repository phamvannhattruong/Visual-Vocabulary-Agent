"""Conversational tutor API endpoints."""
import json
from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.app.schemas import ChatRequest, ChatResponse
from backend.app.db.crud import background_save_chat_log

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


def _extract_last_user_message(messages: list[dict[str, str]]) -> str:
    """Extract latest user question from the conversation payload."""
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


@router.post("/chat-bot", response_model=ChatResponse)
@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
):
    user_message = _extract_last_user_message(request.messages)
    try:
        reply = get_chat_agent().generate_response(with_system_prompt(request.messages))
        client_ip = http_request.client.host if http_request.client else None

        # Asynchronously persist chat log to database
        background_tasks.add_task(
            background_save_chat_log,
            session_id=request.session_id,
            user_message=user_message,
            bot_response=reply,
            user_id=request.user_id,
            ip_address=client_ip,
        )
        return ChatResponse(reply=reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot failed to generate response: {exc}") from exc


@router.post("/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    http_request: Request,
):
    user_message = _extract_last_user_message(request.messages)
    client_ip = http_request.client.host if http_request.client else None

    try:
        def event_stream():
            collected_chunks = []
            try:
                for chunk in get_chat_agent().stream_response(with_system_prompt(request.messages)):
                    collected_chunks.append(chunk)
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            finally:
                # Save full response when stream finishes
                full_reply = "".join(collected_chunks)
                background_save_chat_log(
                    session_id=request.session_id,
                    user_message=user_message,
                    bot_response=full_reply,
                    user_id=request.user_id,
                    ip_address=client_ip,
                )
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Streaming failed: {exc}") from exc
