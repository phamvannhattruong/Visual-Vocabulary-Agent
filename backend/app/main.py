from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

# Import the API router
from backend.app.api.endpoints import router as api_router

app = FastAPI(title="Visual Vocabulary Agent API")

# Define paths relative to this file
# D:\Study\My_project\Visual_Vocabulary_Agent\backend\app\main.py -> BASE_DIR is D:\Study\My_project\Visual_Vocabulary_Agent
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files (includes uploads)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configure templates
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "template"))

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get('/learn-image')
async def learn_image(request: Request):
    return templates.TemplateResponse("imagelearn.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
