from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import os
import shutil
import re
import json
from pathlib import Path
from backend.app.api.utils import save_upload_file, extract_quiz, extract_json_from_ai
from typing import List, Dict

# Import agents
from backend.app.agents.vision_agent import DetectAgent
from backend.app.agents.teacher_agent import TeacherAgent
from backend.app.agents.voice_agent import VoiceAgent
from backend.app.agents.chat_agent import ChatAgent

# Import Schemas
from backend.app.schemas import ChatRequest, ChatResponse

# Import Utils Functions
from backend.app.api.utils import get_relative_url, build_message_list

router = APIRouter()

# Initialize agents
vision_agent = DetectAgent()
teacher_agent = TeacherAgent()
voice_agent = VoiceAgent()
chat_agent = ChatAgent(
    repo_id="DeeplearningVN/Chatbot_English",
    filename="meta-llama-3.1-8b.Q4_K_M.gguf",
    n_ctx=2048,
    n_gpu_layers=10
)

# --- API ENDPOINTS ---

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_path = save_upload_file(file)
    labels, annotated_path = vision_agent.detect_objects(file_path)

    if not annotated_path:
        raise HTTPException(status_code=500, detail="Failed to process image")

    try:
        raw_response = teacher_agent.generate_learning_content(labels)
        lesson_text, quiz_data = extract_quiz(raw_response)
    except Exception as e:
        print(f"Teacher Agent Error: {e}")
        lesson_text = "Sorry, I couldn't generate a lesson right now."
        quiz_data = None

    return {
        "file_name": file.filename,
        "detected_label": [str(x) for x in labels],
        "annotated_img_url": get_relative_url(annotated_path),
        "lesson_context": lesson_text,
        "quiz": quiz_data,
        "success": True
    }


@router.post("/evaluate-pronunciation")
async def evaluate_pronunciation(
    target_word: str = Form(...),
    audio_file: UploadFile = File(...),
):
    try:
        audio_bytes = await audio_file.read()
        evaluation_raw = voice_agent.check_speech(target_word, audio_bytes)
        evaluation_data = extract_json_from_ai(evaluation_raw)

        if not evaluation_data:
            return {"feedback": evaluation_raw, "score": 0, "tip": "Please try again."}

        return evaluation_data
    except Exception as e:
        print(f"Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Agent error: {str(e)}")


@router.post("/chat-bot", response_model=ChatResponse)
@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        # request.messages đã là List[Dict[str, str]] chuẩn format LLM
        bot_response = chat_agent.generate_response(request.messages)

        # Trả về đúng field 'reply' theo ChatResponse schema
        return ChatResponse(reply=bot_response)
    except Exception as e:
        print(f"Chat Agent Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Chatbot failed to generate response: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    try:
        def event_stream():
            if hasattr(chat_agent, "generate_stream"):
                for chunk in chat_agent.generate_stream(request.messages):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            else:
                full_text = chat_agent.generate_response(request.messages)
                yield f"data: {json.dumps({'content': full_text})}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        print(f"Stream Error: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")