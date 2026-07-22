from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import shutil
import re
import json
from pathlib import Path
from backend.app.api.utils import save_upload_file, extract_quiz, extract_json_from_ai

# Import agents
from backend.app.agents.vision_agent import DetectAgent
from backend.app.agents.teacher_agent import TeacherAgent
from backend.app.agents.voice_agent import VoiceAgent

router = APIRouter()

# Initialize agents
vision_agent = DetectAgent()
teacher_agent = TeacherAgent()
voice_agent = VoiceAgent()

def get_relative_url(absolute_path: str) -> str:
    """Converts an absolute path within static/ to a relative URL."""
    path_obj = Path(absolute_path)
    try:
        # Find 'static' in the path and return everything from there
        parts = path_obj.parts
        static_index = parts.index("static")
        return "/" + "/".join(parts[static_index:])
    except ValueError:
        return absolute_path

# --- API ENDPOINTS ---
@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save original file
    file_path = save_upload_file(file)
    
    # Detect objects and save annotated image
    labels, annotated_path = vision_agent.detect_objects(file_path)

    if not annotated_path:
         raise HTTPException(status_code=500, detail="Failed to process image")

    # Generate lesson content
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

        # Clean and parse JSON
        evaluation_data = extract_json_from_ai(evaluation_raw)

        if not evaluation_data:
            # Fallback if JSON extraction fails but we have text
            return {"feedback": evaluation_raw, "score": 0, "tip": "Please try again."}

        return evaluation_data
    except Exception as e:
        print(f"Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Agent error: {str(e)}")
