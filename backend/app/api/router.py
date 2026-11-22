"""Central router configuration and registration for REST APIs and SSR web pages."""
from fastapi import APIRouter, FastAPI

from backend.app.api.routes import chat, learning, logs
from backend.app.api.views import pages

# API router aggregating REST endpoints under /api/v1
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(learning.router)
api_router.include_router(chat.router)
api_router.include_router(logs.router)


def register_routers(app: FastAPI) -> None:
    """Register all REST API routers and Web Page routers onto the main FastAPI application."""
    # Register REST APIs
    app.include_router(learning.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(logs.router, prefix="/api/v1")

    # Register Server-Side Rendered Web Pages
    app.include_router(pages.router)
