"""Streamlit session state helpers for authentication and sidebar rendering."""

from __future__ import annotations

import logging
import time
from typing import Optional

import streamlit as st

from config.settings import settings
from database.db import get_session_factory, init_db
from models.user import User
from services.auth_service import auth_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

# Cache duration for health checks (seconds)
_HEALTH_CHECK_CACHE_TTL: int = 60


def init_app_state() -> None:
    """
    Initialize database and session state defaults.

    Safe to call multiple times; only performs initialization once per
    Streamlit session.
    """
    try:
        if "db_initialized" not in st.session_state:
            init_db()
            st.session_state.db_initialized = True

        defaults = {
            "logged_in": False,
            "user_id": None,
            "username": None,
            "email": None,
            "groq_model": settings.GROQ_MODEL,
            "interview_session_id": None,
            "current_question_id": None,
            "current_question_number": 0,
            "interview_answers_count": 0,
            "last_evaluation": None,
            "feedback_session_id": None,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    except Exception as exc:
        logger.exception("init_app_state failed: %s", exc)
        st.error(f"Application initialization failed: {exc}")


def login_user(user: User) -> None:
    """
    Set session state after successful login.

    Args:
        user: Authenticated User ORM instance.
    """
    try:
        st.session_state.logged_in = True
        st.session_state.user_id = user.id
        st.session_state.username = user.username
        st.session_state.email = user.email
    except Exception as exc:
        logger.exception("login_user failed: %s", exc)


def logout_user() -> None:
    """Clear all authentication and interview session state."""
    try:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.interview_session_id = None
        st.session_state.current_question_id = None
        st.session_state.current_question_number = 0
        st.session_state.interview_answers_count = 0
        st.session_state.last_evaluation = None
        st.session_state.feedback_session_id = None
    except Exception as exc:
        logger.exception("logout_user failed: %s", exc)


def require_login() -> bool:
    """
    Guard for pages that require authentication.

    Redirects unauthenticated users to the login page and halts
    page execution with ``st.stop()``.

    Returns:
        True if user is logged in (never returns False; calls st.stop instead).
    """
    try:
        init_app_state()
        if not st.session_state.get("logged_in"):
            st.warning("Please log in to access this page.")
            st.page_link("pages/1_login.py", label="Go to Login", icon="🔐")
            st.stop()
        return True
    except SystemExit:
        # st.stop() raises SystemExit — let it propagate
        raise
    except Exception as exc:
        logger.exception("require_login failed: %s", exc)
        st.error("Authentication check failed.")
        st.stop()
        return False


def _cached_health_check() -> bool:
    """
    Check Groq API health with a TTL cache to avoid hammering the server.

    Returns:
        True if Groq API is reachable (cached result within TTL).
    """
    now = time.time()
    last_check = st.session_state.get("_groq_health_ts", 0.0)
    if now - last_check < _HEALTH_CHECK_CACHE_TTL:
        return st.session_state.get("_groq_health", False)
    try:
        healthy = llm_service.check_health()
        st.session_state["_groq_health"] = healthy
        st.session_state["_groq_health_ts"] = now
        return healthy
    except Exception as exc:
        logger.warning("_cached_health_check failed: %s", exc)
        st.session_state["_groq_health"] = False
        st.session_state["_groq_health_ts"] = now
        return False


def render_sidebar() -> None:
    """
    Render common sidebar with user info, model selector, and health indicator.

    Uses cached health checks to avoid latency on every page load.
    """
    try:
        init_app_state()
        with st.sidebar:
            st.markdown("### ⚙️ Settings")
            if st.session_state.get("logged_in"):
                st.markdown(f"**User:** {st.session_state.username}")

            # --- Model Switcher ---
            st.markdown("---")
            st.markdown("#### 🤖 Model")

            is_healthy = _cached_health_check()
            if is_healthy:
                st.success("Groq API connected")
            else:
                st.error("Groq API unreachable")

            # Build model list from settings
            all_models = llm_service.list_models()
            current_model = st.session_state.get("groq_model", settings.GROQ_MODEL)

            if all_models:
                # Determine current index for default selection
                try:
                    current_idx = all_models.index(current_model)
                except ValueError:
                    current_idx = 0

                picked = st.selectbox(
                    "Switch model",
                    all_models,
                    index=current_idx,
                    help="Select a Groq-hosted model",
                )
                if picked and picked != current_model:
                    st.session_state.groq_model = picked
                    llm_service.set_model(picked)
                    st.rerun()
            else:
                # Fallback: manual text input if no models available
                model = st.text_input(
                    "Model name",
                    value=current_model,
                    help="Enter model name manually (e.g. llama3-70b-8192)",
                )
                if model and model != current_model:
                    st.session_state.groq_model = model
                    llm_service.set_model(model)

            st.caption(f"Active: **{st.session_state.get('groq_model', settings.GROQ_MODEL)}**")

            if st.session_state.get("logged_in"):
                if st.button("Logout", type="secondary"):
                    logout_user()
                    st.rerun()
    except Exception as exc:
        logger.exception("render_sidebar failed: %s", exc)


def get_db_session():
    """
    Return a new SQLAlchemy session.

    Callers are responsible for closing the session (use try/finally).

    Returns:
        A new SQLAlchemy Session instance.
    """
    return get_session_factory()()
