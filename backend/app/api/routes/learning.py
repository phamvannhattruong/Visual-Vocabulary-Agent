"""Image-analysis and pronunciation API endpoints."""
import logging
from functools import lru_cache
from typing import Optional, TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from httpx import TimeoutException
from sqlalchemy.orm import Session

from backend.app.core.settings import UPLOAD_DIR
from backend.app.db.session import get_db
from backend.app.db.crud import (
    background_save_image_log,
    background_save_pronunciation_log,
    get_user_learning_memory,
)
from backend.app.schemas.learning import SynonymLessonRequest, SynonymLessonResponse
from backend.app.schemas.pronunciation import PronunciationEvaluation
from backend.app.utils.audio import InvalidRecording, MAX_RECORDING_BYTES, prepare_pronunciation_audio
from backend.app.utils.content import (
    extract_quiz,
    get_relative_url,
    save_upload_file,
)

router = APIRouter(tags=["learning"])
logger = logging.getLogger(__name__)

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
    scan_mode: str = Form("auto"),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_path = save_upload_file(file)
    labels, annotated_path, detected_objects, scene_context = get_vision_agent().detect_hybrid(
        file_path, scan_mode=scan_mode
    )
    if not annotated_path:
        raise HTTPException(status_code=500, detail="Failed to process image")

    # Retrieve learner's personalized long-term memory profile
    user_memory = get_user_learning_memory(db=db, user_id=user_id)

    try:
        raw_response = get_teacher_agent().generate_learning_content(
            labels, scene_context=scene_context, user_memory=user_memory
        )
        lesson_text, quiz_data = extract_quiz(raw_response)
    except Exception as exc:
        logging.getLogger("uvicorn.error").warning(
            f"TeacherAgent online generation error: {exc}. Activating robust local lesson generator."
        )
        try:
            raw_response = get_teacher_agent().build_offline_lesson(
                labels, scene_context=scene_context, user_memory=user_memory
            )
            lesson_text, quiz_data = extract_quiz(raw_response)
        except Exception:
            lesson_text, quiz_data = "Chào mừng bạn! Hãy tiếp tục khám phá các từ vựng thú vị nhé.", None

    annotated_url = get_relative_url(annotated_path)
    client_ip = http_request.client.host if (http_request and http_request.client) else None

    # Persist analysis and lesson log in background with Phase 2 metadata
    background_tasks.add_task(
        background_save_image_log,
        file_name=file.filename,
        detected_labels=labels,
        annotated_img_url=annotated_url,
        lesson_context=lesson_text,
        quiz_data=quiz_data,
        scan_mode=scan_mode,
        detected_objects=detected_objects,
        scene_context=scene_context,
        user_id=user_id,
        ip_address=client_ip,
    )

    return {
        "file_name": file.filename,
        "detected_label": [str(label) for label in labels],
        "detected_objects": detected_objects,
        "scene_context": scene_context,
        "scan_mode": scan_mode,
        "user_memory": user_memory,
        "annotated_img_url": annotated_url,
        "lesson_context": lesson_text,
        "quiz": quiz_data,
        "success": True,
    }


@router.post("/evaluate-pronunciation", response_model=PronunciationEvaluation)
def evaluate_pronunciation(
    background_tasks: BackgroundTasks,
    http_request: Request,
    target_word: str = Form(..., max_length=200),
    audio_file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
) -> PronunciationEvaluation:
    target_word = target_word.strip()
    if not target_word:
        raise HTTPException(status_code=422, detail="Hãy chọn từ để luyện phát âm.")

    audio_bytes = audio_file.file.read(MAX_RECORDING_BYTES + 1)
    if len(audio_bytes) > MAX_RECORDING_BYTES:
        raise HTTPException(status_code=413, detail="Bản ghi quá lớn. Hãy thu âm ngắn hơn.")

    try:
        wav_bytes = prepare_pronunciation_audio(audio_bytes, audio_file.content_type)
        evaluation = get_voice_agent().check_speech(target_word, wav_bytes)
    except InvalidRecording as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TimeoutError, TimeoutException) as exc:
        raise HTTPException(status_code=504, detail="Chấm phát âm quá thời gian chờ. Hãy thử lại.") from exc
    except Exception as exc:
        logger.warning("Pronunciation evaluation failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Chưa chấm được phát âm. Hãy thử lại.") from exc

    client_ip = http_request.client.host if http_request.client else None
    background_tasks.add_task(
        background_save_pronunciation_log,
        target_word=target_word,
        score=evaluation.score,
        feedback=evaluation.feedback,
        tip=evaluation.tip,
        user_id=user_id,
        ip_address=client_ip,
    )
    return evaluation


@router.post("/synonym-lesson", response_model=SynonymLessonResponse)
async def generate_synonym_lesson(payload: SynonymLessonRequest):
    """Generate or retrieve a mini-lesson for a synonym expansion word."""
    try:
        data = get_teacher_agent().generate_synonym_lesson(payload.word)
        return SynonymLessonResponse(
            word=data.get("word", payload.word),
            ipa=data.get("ipa", ""),
            meaning_vn=data.get("meaning_vn", ""),
            example=data.get("example", ""),
            success=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate synonym lesson: {exc}") from exc
