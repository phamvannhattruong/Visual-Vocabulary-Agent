"""Database session management, engine lifecycle, and connectivity helpers."""
import logging
from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.settings import (
    DATABASE_URL,
    DEFAULT_SQLITE_URL,
    DB_CONNECT_TIMEOUT,
)
from backend.app.db.base import Base
# Ensure all models are registered with Base.metadata
from backend.app.db.models import User, ChatLog, ImageLearningLog, PronunciationLog, ActivityLog

logger = logging.getLogger("backend.app.db")
logging.basicConfig(level=logging.INFO)


def _build_engine(url: str):
    """Build a SQLAlchemy engine with optimized connection options."""
    connect_args = {}
    engine_kwargs = {
        "pool_pre_ping": True,
    }

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif "pyodbc" in url or "mssql" in url:
        connect_args["timeout"] = DB_CONNECT_TIMEOUT
        engine_kwargs["fast_executemany"] = True
    elif "postgresql" in url:
        connect_args["connect_timeout"] = DB_CONNECT_TIMEOUT

    return create_engine(url, connect_args=connect_args, **engine_kwargs)


active_url = DATABASE_URL
is_using_fallback = False
_initialized = False

engine = _build_engine(active_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_initialized():
    """Ensure database connection is validated and schema created exactly once."""
    global engine, active_url, is_using_fallback, SessionLocal, _initialized
    if _initialized:
        return
    _initialized = True

    if not active_url.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"[DATABASE] Connected successfully to primary: {engine.url.drivername}")
        except Exception as conn_err:
            logger.warning(
                f"[DATABASE WARNING] Primary database connection failed ({conn_err}). "
                f"Falling back to local SQLite database at: {DEFAULT_SQLITE_URL}"
            )
            active_url = DEFAULT_SQLITE_URL
            is_using_fallback = True
            engine = _build_engine(active_url)
            SessionLocal.configure(bind=engine)

    try:
        Base.metadata.create_all(bind=engine)
        logger.info(
            f"[DATABASE] Tables verified on {engine.url.drivername} "
            f"({'fallback SQLite' if is_using_fallback else 'primary'})"
        )
    except Exception as exc:
        logger.error(f"[DATABASE ERROR] Could not create tables: {exc}")
        if not is_using_fallback:
            try:
                active_url = DEFAULT_SQLITE_URL
                is_using_fallback = True
                engine = _build_engine(active_url)
                SessionLocal.configure(bind=engine)
                Base.metadata.create_all(bind=engine)
                logger.info("[DATABASE] Fallback SQLite tables created.")
            except Exception as e2:
                logger.error(f"[DATABASE CRITICAL] Fallback also failed: {e2}")


def init_db() -> bool:
    """Initialize database tables, falling back to SQLite if primary DB is unavailable."""
    ensure_initialized()
    return not is_using_fallback


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a transactional database session."""
    ensure_initialized()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_info() -> dict:
    """Returns runtime database status and diagnostic information."""
    ensure_initialized()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            return {
                "connected": True,
                "driver": engine.url.drivername,
                "database": engine.url.database,
                "is_fallback": is_using_fallback,
                "tables": tables,
                "table_count": len(tables),
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "driver": engine.url.drivername,
            "is_fallback": is_using_fallback,
            "tables": [],
            "table_count": 0,
        }
