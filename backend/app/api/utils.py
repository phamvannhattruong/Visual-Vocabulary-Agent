import re
from fastapi import HTTPException
import shutil
import os
import json
from pathlib import Path
from fastapi import File, UploadFile

# Resolve UPLOAD_DIR relative to the project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = BASE_DIR / "frontend" / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(file: UploadFile) -> str:
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return str(file_path)
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
