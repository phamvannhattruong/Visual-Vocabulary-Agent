"""AI agents layer for Visual Vocabulary Agent."""
from backend.app.services.agents.base import Agent
from backend.app.services.agents.vision import DetectAgent
from backend.app.services.agents.teacher import TeacherAgent
from backend.app.services.agents.voice import VoiceAgent
from backend.app.services.agents.chat import ChatAgent

__all__ = [
    "Agent",
    "DetectAgent",
    "TeacherAgent",
    "VoiceAgent",
    "ChatAgent",
]
