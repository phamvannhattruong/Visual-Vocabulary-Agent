import re
from fastapi import HTTPException
import shutil
import os
import json
from fastapi import File, UploadFile

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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