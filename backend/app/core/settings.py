"""Central filesystem and application configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load environment variables from .env
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)

FRONTEND_DIR = PROJECT_ROOT / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
ASSETS_DIR = FRONTEND_DIR / "assets"
UPLOAD_DIR = FRONTEND_DIR / "static" / "uploads"
MODEL_DIR = PROJECT_ROOT / "backend" / "resources" / "models"
DATABASE_DIR = PROJECT_ROOT / "database"

for directory in (UPLOAD_DIR, MODEL_DIR, DATABASE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Database settings
SQLITE_FALLBACK_FILE = DATABASE_DIR / "english_learning_app.db"
DEFAULT_SQLITE_URL = f"sqlite:///{SQLITE_FALLBACK_FILE.as_posix()}"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or not DATABASE_URL.strip():
    DATABASE_URL = DEFAULT_SQLITE_URL

DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "3"))
