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
    UPLOADS_DIR: Path = PROJECT_ROOT / "data" / "uploads"

    # Database
    DB_PATH: str = os.getenv(
        "DB_PATH",
        str(PROJECT_ROOT / "data" / "interview_prep.db"),
    )

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3:14b")
    OLLAMA_PREFERRED_MODELS: list[str] = [
        m.strip()
        for m in os.getenv("OLLAMA_PREFERRED_MODELS", "qwen3:14b,qwen3:32b").split(",")
        if m.strip()
    ]
    OLLAMA_TIMEOUT: int = _get_int("OLLAMA_TIMEOUT", 120)
    OLLAMA_MAX_RETRIES: int = _get_int("OLLAMA_MAX_RETRIES", 3)
    OLLAMA_RETRY_DELAY: float = float(os.getenv("OLLAMA_RETRY_DELAY", "2.0"))

    # Interview
    QUESTIONS_PER_SESSION: int = _get_int("QUESTIONS_PER_SESSION", 10)
    SCORE_INCREASE_THRESHOLD: float = float(
        os.getenv("SCORE_INCREASE_THRESHOLD", "7.0")
    )
    SCORE_DECREASE_THRESHOLD: float = float(
        os.getenv("SCORE_DECREASE_THRESHOLD", "4.0")
    )

    # App
    DEBUG: bool = _get_bool("DEBUG", False)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def ensure_directories(cls) -> None:
        """Create required data directories if they do not exist."""
        try:
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
            cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            cls.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
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
