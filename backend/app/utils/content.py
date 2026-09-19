import re
from fastapi import HTTPException
import shutil
import json
from pathlib import Path
from fastapi import UploadFile
from backend.app.core.settings import UPLOAD_DIR
from backend.app.schemas import ChatRequest
from typing import List, Dict

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

def get_relative_url(absolute_path: str) -> str:
    """Converts an upload file path into its public URL."""
    path_obj = Path(absolute_path)
    try:
        return f"/uploads/{path_obj.relative_to(UPLOAD_DIR).as_posix()}"
    except ValueError:
        return absolute_path

def build_message_list(request: ChatRequest) -> List[Dict[str, str]]:
    """Hỗ trợ cả gửi 1 tin nhắn đơn lẻ hoặc gửi toàn bộ lịch sử chat."""
    if request.messages:
        return [{"role": m.role, "content": m.content} for m in request.messages]
    elif request.message:
        return [{"role": "user", "content": request.message.strip()}]
    else:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp nội dung tin nhắn.")
