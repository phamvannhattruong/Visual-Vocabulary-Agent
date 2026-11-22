"""File storage and URL conversion utilities."""
import shutil
from pathlib import Path
from fastapi import HTTPException, UploadFile

from backend.app.core.settings import UPLOAD_DIR


def save_upload_file(file: UploadFile) -> str:
    """Save an uploaded file to the static upload directory."""
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return str(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")


def get_relative_url(absolute_path: str) -> str:
    """Convert an upload file path into its public URL."""
    path_obj = Path(absolute_path)
    try:
        return f"/uploads/{path_obj.relative_to(UPLOAD_DIR).as_posix()}"
    except ValueError:
        return absolute_path

