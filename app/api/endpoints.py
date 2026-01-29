from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import shutil
import re
import json

# Import các Agent theo cấu trúc thư mục mới
from app.agents.vision_agent import DetectAgent
from app.agents.teacher_agent import TeacherAgent
from app.agents.voice_agent import VoiceAgent

router = APIRouter()

# Khởi tạo Agent
vision_agent = DetectAgent()
teacher_agent = TeacherAgent()
voice_agent = VoiceAgent()

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --- CÁC HÀM TIỆN ÍCH ---
def save_upload_file(file: UploadFile) -> str:
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


def extract_json_from_ai(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group().strip())
        except:
            return None
    return None


def extract_quiz(text: str):
    quiz_match = re.search(r"\[QUIZ_START\](.*?)\[QUIZ_END\]", text, re.DOTALL)
    if quiz_match:
        try:
            quiz_data = json.loads(quiz_match.group(1).strip())
            clean_text = re.sub(r"\[QUIZ_START\].*?\[QUIZ_END\]", "", text, flags=re.DOTALL).strip()
            return clean_text, quiz_data
        except:
            return text, None
    return text, None


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
        user_said: str = Form(...)
):
    try:
        evaluation_raw = voice_agent.check_speech(target_word, user_said)

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