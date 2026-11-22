"""Image-analysis and pronunciation API endpoints."""
from functools import lru_cache
from typing import Optional, TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile

from backend.app.core.settings import UPLOAD_DIR
from backend.app.db.crud import (
    background_save_image_log,
    background_save_pronunciation_log,
)
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
async def analyze_image(
    background_tasks: BackgroundTasks,
    http_request: Request,
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_path = save_upload_file(file)
    labels, annotated_path, detected_objects = get_vision_agent().detect_objects(file_path)
    if not annotated_path:
        raise HTTPException(status_code=500, detail="Failed to process image")

    try:
        raw_response = get_teacher_agent().generate_learning_content(labels)
        lesson_text, quiz_data = extract_quiz(raw_response)
    except Exception:
        lesson_text, quiz_data = "Sorry, I couldn't generate a lesson right now.", None

    annotated_url = get_relative_url(annotated_path)
    client_ip = http_request.client.host if (http_request and http_request.client) else None

    # Persist analysis and lesson log in background
    background_tasks.add_task(
        background_save_image_log,
        file_name=file.filename,
        detected_labels=labels,
        annotated_img_url=annotated_url,
        lesson_context=lesson_text,
        quiz_data=quiz_data,
        user_id=user_id,
        ip_address=client_ip,
    )

    return {
        "file_name": file.filename,
        "detected_label": [str(label) for label in labels],
        "detected_objects": detected_objects,
        "annotated_img_url": annotated_url,
        "lesson_context": lesson_text,
        "quiz": quiz_data,
        "success": True,
    }


@router.post("/evaluate-pronunciation")
async def evaluate_pronunciation(
    background_tasks: BackgroundTasks,
    http_request: Request,
    target_word: str = Form(...),
    audio_file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
):
    try:
        evaluation_raw = get_voice_agent().check_speech(target_word, await audio_file.read())
        eval_result = extract_json_from_ai(evaluation_raw) or {
            "feedback": evaluation_raw,
            "score": 0,
            "tip": "Please try again.",
        }

        client_ip = http_request.client.host if (http_request and http_request.client) else None

        # Persist pronunciation evaluation log in background
        background_tasks.add_task(
            background_save_pronunciation_log,
            target_word=target_word,
            score=eval_result.get("score"),
            feedback=eval_result.get("feedback"),
            tip=eval_result.get("tip"),
            user_id=user_id,
            ip_address=client_ip,
        )

        return eval_result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI Agent error: {exc}") from exc
