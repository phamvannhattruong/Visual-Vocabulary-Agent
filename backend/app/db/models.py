"""SQLAlchemy models for application database logging and user progress."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, DateTime, ForeignKey
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy.orm import relationship

from backend.app.db.base import Base

# Universal Unicode text type that translates to NVARCHAR(MAX) on MSSQL and TEXT on SQLite/Postgres
UnicodeLongText = UnicodeText().with_variant(NVARCHAR(None), "mssql")


class User(Base):
    """User account entity matching database/scripts/create_db.sql."""
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(Unicode(50), nullable=True, unique=False)
    create_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")
    image_learning_logs = relationship("ImageLearningLog", back_populates="user", cascade="all, delete-orphan")
    pronunciation_logs = relationship("PronunciationLog", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class ChatLog(Base):
    """Stores conversation history between user and AI English tutor."""
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    user_message = Column(UnicodeLongText, nullable=False)
    bot_response = Column(UnicodeLongText, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="chat_logs")


class ImageLearningLog(Base):
    """Stores visual vocabulary lesson generation results from uploaded/captured images."""
    __tablename__ = "image_learning_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name = Column(Unicode(255), nullable=True)
    detected_labels = Column(UnicodeLongText, nullable=True)  # JSON-encoded array of detected objects
    annotated_img_url = Column(Unicode(500), nullable=True)
    lesson_context = Column(UnicodeLongText, nullable=True)
    quiz_data = Column(UnicodeLongText, nullable=True)  # JSON-encoded quiz question & options
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="image_learning_logs")


class PronunciationLog(Base):
    """Stores pronunciation evaluation scores, feedback and tips."""
    __tablename__ = "pronunciation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="SET NULL"), nullable=True, index=True)
    target_word = Column(Unicode(100), nullable=False, index=True)
    score = Column(Integer, nullable=True)
    feedback = Column(UnicodeLongText, nullable=True)
    tip = Column(UnicodeLongText, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="pronunciation_logs")


class ActivityLog(Base):
    """General audit/activity log for user operations and API calls."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(Unicode(100), nullable=False, index=True)  # e.g. "CHAT", "ANALYZE_IMAGE", "PRONUNCIATION"
    status = Column(Unicode(50), nullable=False, default="SUCCESS")
    details = Column(UnicodeLongText, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="activity_logs")

