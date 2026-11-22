"""FastAPI main application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import register_routers
from backend.app.core.settings import ASSETS_DIR, UPLOAD_DIR
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection and schemas on app startup
    init_db()
    yield


app = FastAPI(
    title="Visual Vocabulary Agent API",
    description="Multi-Agent AI and Computer Vision English Learning Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# Mount static asset and upload directories
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Register all routes (REST APIs + SSR Web Pages)
register_routers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
