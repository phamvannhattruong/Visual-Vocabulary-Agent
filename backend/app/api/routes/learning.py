"""Image-analysis and pronunciation API endpoints."""
from functools import lru_cache
from typing import TYPE_CHECKING

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.core.settings import UPLOAD_DIR
from backend.app.utils.content import (
    extract_json_from_ai,
    extract_quiz,
    get_relative_url,
    save_upload_file,
)

router = APIRouter(tags=["learning"])

if TYPE_CHECKING:
    from backend.app.services.agents.teacher import TeacherAgent
    from backend.app.services.agents.vision import DetectAgent
    from backend.app.services.agents.voice import VoiceAgent


@lru_cache
def get_vision_agent() -> "DetectAgent":
    from backend.app.services.agents.vision import DetectAgent

    return DetectAgent()


@lru_cache
def get_teacher_agent() -> "TeacherAgent":
    from backend.app.services.agents.teacher import TeacherAgent

    return TeacherAgent()


@lru_cache
def get_voice_agent() -> "VoiceAgent":
    from backend.app.services.agents.voice import VoiceAgent

    return VoiceAgent()


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_path = save_upload_file(file)
    labels, annotated_path = get_vision_agent().detect_objects(file_path)
    if not annotated_path:
        raise HTTPException(status_code=500, detail="Failed to process image")

    try:
        raw_response = get_teacher_agent().generate_learning_content(labels)
        lesson_text, quiz_data = extract_quiz(raw_response)
    except Exception:
        lesson_text, quiz_data = "Sorry, I couldn't generate a lesson right now.", None

    return {
        "file_name": file.filename,
        "detected_label": [str(label) for label in labels],
        "annotated_img_url": get_relative_url(annotated_path),
        "lesson_context": lesson_text,
        "quiz": quiz_data,
        "success": True,
    }


@router.post("/evaluate-pronunciation")
async def evaluate_pronunciation(
    target_word: str = Form(...), audio_file: UploadFile = File(...)
):
    try:
        evaluation_raw = get_voice_agent().check_speech(target_word, await audio_file.read())
        return extract_json_from_ai(evaluation_raw) or {
            "feedback": evaluation_raw,
            "score": 0,
            "tip": "Please try again.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI Agent error: {exc}") from exc
