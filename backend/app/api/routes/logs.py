"""Database status and log viewing endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db, get_db_info
from backend.app.db.crud import (
    get_chat_logs,
    get_image_logs,
    get_pronunciation_logs,
    get_activity_logs,
)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/status")
def get_database_status():
    """Check database connection health and schema status."""
    info = get_db_info()
    return {
        "status": "healthy" if info.get("connected") else "unhealthy",
        "database": info,
    }


@router.get("/chat")
def list_chat_logs(
    session_id: Optional[str] = Query(None, description="Filter by chat session ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve recent chat conversation logs."""
    logs = get_chat_logs(db=db, session_id=session_id, limit=limit)
    return [
        {
            "id": log.id,
            "session_id": log.session_id,
            "user_id": log.user_id,
            "user_message": log.user_message,
            "bot_response": log.bot_response,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/learning")
def list_image_learning_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve recent image learning & vocabulary analysis logs."""
    logs = get_image_logs(db=db, limit=limit)
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "file_name": log.file_name,
            "detected_labels": log.detected_labels,
            "annotated_img_url": log.annotated_img_url,
            "lesson_context": log.lesson_context,
            "quiz_data": log.quiz_data,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/pronunciation")
def list_pronunciation_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve recent pronunciation evaluation logs."""
    logs = get_pronunciation_logs(db=db, limit=limit)
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "target_word": log.target_word,
            "score": log.score,
            "feedback": log.feedback,
            "tip": log.tip,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/activities")
def list_activity_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve recent audit and activity logs."""
    logs = get_activity_logs(db=db, limit=limit)
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "status": log.status,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
