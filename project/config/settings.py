"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root (parent of config/)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Load .env from project root
_env_path: Path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()


def _get_bool(key: str, default: bool = False) -> bool:
    """Parse boolean from environment variable."""
    val: str = os.getenv(key, str(default)).lower()
    return val in ("1", "true", "yes", "on")


def _get_int(key: str, default: int) -> int:
    """Parse integer from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


class Settings:
    """Centralized application settings."""

    # Paths
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    REPORTS_DIR: Path = PROJECT_ROOT / "data" / "reports"

    # App
    APP_NAME: str = os.getenv("APP_NAME", "AI Interview Prep")
    DEBUG: bool = _get_bool("DEBUG", False)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")

    # Groq LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    AVAILABLE_MODELS: list[str] = [
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
    ]

    # Supabase
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # Interview
    QUESTIONS_PER_SESSION: int = _get_int("QUESTIONS_PER_SESSION", 10)
    SCORE_INCREASE_THRESHOLD: float = float(
        os.getenv("SCORE_INCREASE_THRESHOLD", "7.0")
    )
    SCORE_DECREASE_THRESHOLD: float = float(
        os.getenv("SCORE_DECREASE_THRESHOLD", "4.0")
    )

    @classmethod
    def ensure_directories(cls) -> None:
        """Create required data directories if they do not exist."""
        try:
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
            cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logging.getLogger(__name__).error(
                "Failed to create directories: %s", exc
            )
            raise


def configure_logging() -> None:
    """Configure root logger based on settings."""
    level: int = getattr(
        logging,
        Settings.LOG_LEVEL.upper(),
        logging.INFO,
    )
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if Settings.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)


settings = Settings()
