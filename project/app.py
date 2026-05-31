"""AI-Powered Interview Preparation and Evaluation System — Main Entry."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import configure_logging, settings
from utils.streamlit_auth import init_app_state, logout_user, render_sidebar

configure_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Interview Prep",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    init_app_state()
    settings.ensure_directories()
except Exception as exc:
    logger.exception("Startup failed: %s", exc)
    st.error(f"Startup error: {exc}")
    st.stop()

render_sidebar()

st.title("🎯 AI Interview Preparation & Evaluation")
st.markdown(
    """
Welcome to your **production-ready** AI interview coaching platform.

### Features
- **Resume Analysis** — Upload PDF, extract skills, projects, education
- **Adaptive Interviews** — 5 types, 3 difficulty levels, 10 questions per session
- **AI Evaluation** — Scores, strengths, weaknesses, model answers, follow-ups
- **Analytics Dashboard** — Plotly charts and performance trends
- **PDF Reports** — Downloadable interview reports via ReportLab

### Get Started
1. [Register](pages/2_register.py) a new account or [Login](pages/1_login.py)
2. Upload your [Resume](pages/3_resume.py)
3. Start an [Interview](pages/4_interview.py)
4. Review [Feedback](pages/5_feedback.py), [Analytics](pages/6_analytics.py), and [Reports](pages/7_report.py)
"""
)

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/1_login.py", label="Login", icon="🔐")
with col2:
    st.page_link("pages/2_register.py", label="Register", icon="📝")
with col3:
    if st.session_state.get("logged_in"):
        st.page_link("pages/4_interview.py", label="Start Interview", icon="🎤")

if st.session_state.get("logged_in"):
    st.success(f"Logged in as **{st.session_state.username}**")
    st.info("Use the sidebar to switch Ollama models or log out.")
else:
    st.warning("You are not logged in. Please register or login to continue.")

st.divider()
st.caption(
    f"Ollama: {settings.OLLAMA_BASE_URL} | Model: {st.session_state.get('ollama_model', settings.OLLAMA_DEFAULT_MODEL)}"
)
