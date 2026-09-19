"""Central filesystem configuration for the application."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
ASSETS_DIR = FRONTEND_DIR / "assets"
UPLOAD_DIR = FRONTEND_DIR / "static" / "uploads"
MODEL_DIR = PROJECT_ROOT / "backend" / "resources" / "models"

for directory in (UPLOAD_DIR, MODEL_DIR):
    directory.mkdir(parents=True, exist_ok=True)
