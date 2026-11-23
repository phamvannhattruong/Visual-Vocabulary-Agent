"""Database CRUD operations and background logging services."""
import json
import logging
from typing import Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db.models import User, ChatLog, ImageLearningLog, PronunciationLog, ActivityLog
from backend.app.db.session import SessionLocal

logger = logging.getLogger("backend.app.db.crud")


# ---------------------------------------------------------
# User Operations
# ---------------------------------------------------------

def get_or_create_user(db: Session, username: str) -> User:
    """Find an existing user or create a new user profile."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ---------------------------------------------------------
# Synchronous Logging Functions (using provided Session)
# ---------------------------------------------------------

def log_chat(
    db: Session,
    session_id: Optional[str],
    user_message: str,
    bot_response: Optional[str],
    user_id: Optional[int] = None,
) -> ChatLog:
    """Save a chat interaction log."""
    chat_log = ChatLog(
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
        user_id=user_id,
    )
    db.add(chat_log)
    db.commit()
    db.refresh(chat_log)
    return chat_log


def log_image_learning(
    db: Session,
    file_name: Optional[str],
    detected_labels: Any,
    annotated_img_url: Optional[str],
    lesson_context: Optional[str],
    quiz_data: Any,
    scan_mode: Optional[str] = "auto",
    detected_objects: Any = None,
    scene_context: Any = None,
    user_id: Optional[int] = None,
) -> ImageLearningLog:
    """Save an image analysis and lesson generation log with Phase 2 metadata."""
    # Ensure serializable labels, objects, scene, and quiz data
    if isinstance(detected_labels, (list, tuple, set)):
        labels_str = json.dumps([str(l) for l in detected_labels], ensure_ascii=False)
    elif isinstance(detected_labels, str):
        labels_str = detected_labels
    else:
        labels_str = None

    if isinstance(quiz_data, (dict, list)):
        quiz_str = json.dumps(quiz_data, ensure_ascii=False)
    elif isinstance(quiz_data, str):
        quiz_str = quiz_data
    else:
        quiz_str = None

    if isinstance(detected_objects, (list, tuple)):
        objects_str = json.dumps(detected_objects, ensure_ascii=False)
    elif isinstance(detected_objects, str):
        objects_str = detected_objects
    else:
        objects_str = None

    if isinstance(scene_context, dict):
        scene_str = json.dumps(scene_context, ensure_ascii=False)
    elif isinstance(scene_context, str):
        scene_str = scene_context
    else:
        scene_str = None

    image_log = ImageLearningLog(
        user_id=user_id,
        file_name=file_name,
        scan_mode=scan_mode or "auto",
        detected_labels=labels_str,
        detected_objects=objects_str,
        scene_context=scene_str,
        annotated_img_url=annotated_img_url,
        lesson_context=lesson_context,
        quiz_data=quiz_str,
    )
    db.add(image_log)
    db.commit()
    db.refresh(image_log)
    return image_log


def log_pronunciation(
    db: Session,
    target_word: str,
    score: Optional[int],
    feedback: Optional[str],
    tip: Optional[str],
    user_id: Optional[int] = None,
) -> PronunciationLog:
    """Save a pronunciation evaluation log."""
    pron_log = PronunciationLog(
        user_id=user_id,
        target_word=target_word,
        score=score,
        feedback=feedback,
        tip=tip,
    )
    db.add(pron_log)
    db.commit()
    db.refresh(pron_log)
    return pron_log


def log_activity(
    db: Session,
    action: str,
    status: str = "SUCCESS",
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_id: Optional[int] = None,
) -> ActivityLog:
    """Record a general system/user activity log."""
    activity = ActivityLog(
        action=action,
        status=status,
        details=details,
        ip_address=ip_address,
        user_id=user_id,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# ---------------------------------------------------------
# Background Task Helpers (FastAPI BackgroundTasks safe)
# ---------------------------------------------------------

def background_save_chat_log(
    session_id: Optional[str],
    user_message: str,
    bot_response: Optional[str],
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
):
    """Safely log chat message and activity in background without blocking response."""
    with SessionLocal() as db:
        try:
            log_chat(
                db=db,
                session_id=session_id,
                user_message=user_message,
                bot_response=bot_response,
                user_id=user_id,
            )
            log_activity(
                db=db,
                action="CHAT",
                status="SUCCESS",
                details=f"Chat session: {session_id or 'none'}",
                ip_address=ip_address,
                user_id=user_id,
            )
        except Exception as exc:
            logger.error(f"[DB LOG ERROR] Failed to save chat log: {exc}")


def background_save_image_log(
    file_name: Optional[str],
    detected_labels: Any,
    annotated_img_url: Optional[str],
    lesson_context: Optional[str],
    quiz_data: Any,
    scan_mode: Optional[str] = "auto",
    detected_objects: Any = None,
    scene_context: Any = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
):
    """Safely log image analysis and lesson generation in background with Phase 2 metadata."""
    with SessionLocal() as db:
        try:
            log_image_learning(
                db=db,
                file_name=file_name,
                detected_labels=detected_labels,
                annotated_img_url=annotated_img_url,
                lesson_context=lesson_context,
                quiz_data=quiz_data,
                scan_mode=scan_mode,
                detected_objects=detected_objects,
                scene_context=scene_context,
                user_id=user_id,
            )
            log_activity(
                db=db,
                action="ANALYZE_IMAGE",
                status="SUCCESS",
                details=f"File: {file_name}, ScanMode: {scan_mode or 'auto'}",
                ip_address=ip_address,
                user_id=user_id,
            )
        except Exception as exc:
            logger.error(f"[DB LOG ERROR] Failed to save image log: {exc}")


def background_save_pronunciation_log(
    target_word: str,
    score: Optional[int],
    feedback: Optional[str],
    tip: Optional[str],
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
):
    """Safely log pronunciation evaluation in background."""
    with SessionLocal() as db:
        try:
            log_pronunciation(
                db=db,
                target_word=target_word,
                score=score,
                feedback=feedback,
                tip=tip,
                user_id=user_id,
            )
            log_activity(
                db=db,
                action="EVALUATE_PRONUNCIATION",
                status="SUCCESS",
                details=f"Target: {target_word}, Score: {score}",
                ip_address=ip_address,
                user_id=user_id,
            )
        except Exception as exc:
            logger.error(f"[DB LOG ERROR] Failed to save pronunciation log: {exc}")


# ---------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------

def get_chat_logs(db: Session, session_id: Optional[str] = None, limit: int = 50) -> List[ChatLog]:
    """Retrieve recent chat logs, optionally filtered by session_id."""
    query = db.query(ChatLog)
    if session_id:
        query = query.filter(ChatLog.session_id == session_id)
    return query.order_by(desc(ChatLog.created_at)).limit(limit).all()


def get_image_logs(db: Session, limit: int = 50) -> List[ImageLearningLog]:
    """Retrieve recent image learning logs."""
    return db.query(ImageLearningLog).order_by(desc(ImageLearningLog.created_at)).limit(limit).all()


def get_pronunciation_logs(db: Session, limit: int = 50) -> List[PronunciationLog]:
    """Retrieve recent pronunciation evaluation logs."""
    return db.query(PronunciationLog).order_by(desc(PronunciationLog.created_at)).limit(limit).all()


def get_activity_logs(db: Session, limit: int = 50) -> List[ActivityLog]:
    """Retrieve recent application activity logs."""
    return db.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(limit).all()

