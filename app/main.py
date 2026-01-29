import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import router as api_router
import os

app = FastAPI(
    title = "Visual Vocabulary Agent",
    Description = "This is a app to learn English which uses Yolo to detect objects in images and a Agent to generate English lesson",
    version = "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

directories = ["static/uploads", "static/results", "models"]
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(api_router, prefix="/api/v1")

async def root():
    return {
        "message": "Welcome to English Learning",
        "docs": "/docs",
        "status": "running"
    }

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)