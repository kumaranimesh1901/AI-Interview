"""SQLAlchemy database engine and session management."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Create or return the singleton SQLAlchemy engine."""
    global _engine
    try:
        if _engine is None:
            settings.ensure_directories()
            db_url: str = f"sqlite:///{settings.DB_PATH}"
            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                echo=settings.DEBUG,
            )

            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
                """Enable foreign keys for SQLite."""
                try:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
                except Exception as exc:
                    logger.warning("Could not set SQLite pragma: %s", exc)

            logger.info("Database engine created at %s", settings.DB_PATH)
        return _engine
    except Exception as exc:
        logger.exception("Failed to create database engine: %s", exc)
        raise


def get_session_factory() -> sessionmaker[Session]:
    """Return session factory bound to engine."""
    global _SessionLocal
    try:
        if _SessionLocal is None:
            _SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=get_engine(),
            )
        return _SessionLocal
    except Exception as exc:
        logger.exception("Failed to create session factory: %s", exc)
        raise


def init_db() -> None:
    """Create all tables from registered models."""
    try:
        # Import models so they register with Base.metadata
        import models.analytics  # noqa: F401
        import models.interview  # noqa: F401
        import models.resume  # noqa: F401
        import models.user  # noqa: F401

        settings.ensure_directories()
        Base.metadata.create_all(bind=get_engine())
        logger.info("Database tables initialized")
    except Exception as exc:
        logger.exception("Failed to initialize database: %s", exc)
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager yielding a database session with commit/rollback."""
    session: Session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception("Database session error: %s", exc)
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Generator for dependency-style session access."""
    session: Session = get_session_factory()()
    try:
        yield session
    except Exception as exc:
        session.rollback()
        logger.exception("Database error: %s", exc)
        raise
    finally:
        session.close()
