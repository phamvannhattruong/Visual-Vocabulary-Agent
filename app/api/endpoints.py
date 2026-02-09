from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import shutil
import re
import json
from app.api.utils import *


# Import các Agent theo cấu trúc thư mục mới
from app.agents.vision_agent import DetectAgent
from app.agents.teacher_agent import TeacherAgent
from app.agents.voice_agent import VoiceAgent

router = APIRouter()

# Khởi tạo Agent
vision_agent = DetectAgent()
teacher_agent = TeacherAgent()
voice_agent = VoiceAgent()

# --- API ENDPOINTS ---
@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_path = save_upload_file(file)
    labels, annotated_path = vision_agent.detect_objects(file_path)

    try:
        raw_response = teacher_agent.generate_learning_content(labels)
        lesson_text, quiz_data = extract_quiz(raw_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent error: {e}")

    return {
        "file_name": file.filename,
        "detected_label": [str(x) for x in labels],
        "annotated_img_path": str(annotated_path),
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

        # Làm sạch và parse JSON
        evaluation_data = extract_json_from_ai(evaluation_raw)

        if not evaluation_data:
            raise ValueError("AI returned invalid JSON format")

        json_match = re.search(r"\{.*\}", evaluation_raw, re.DOTALL)
        return json.loads(json_match.group())
    except Exception as e:
        # Log lỗi ra console để dễ debug
        print(f"Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Agent error: {e}")