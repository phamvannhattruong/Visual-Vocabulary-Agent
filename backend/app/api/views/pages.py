"""Jinja2 template view controllers for server-side rendered pages."""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from backend.app.core.settings import TEMPLATES_DIR

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/")
async def root(request: Request):
    """Render main application dashboard."""
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/learn-image")
async def learn_image(request: Request):
    """Render visual vocabulary image learning studio."""
    return templates.TemplateResponse(request=request, name="imagelearn.html")


@router.get("/chat-bot")
async def chat_bot(request: Request):
    """Render interactive AI phonetic & grammar tutor chat interface."""
    return templates.TemplateResponse(request=request, name="chatbot.html")


@router.get("/ipa")
async def ipa_chart(request: Request):
    """Render international phonetic alphabet interactive chart."""
    return templates.TemplateResponse(request=request, name="ipa.html")

