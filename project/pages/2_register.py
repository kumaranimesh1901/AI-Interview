"""Registration page."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import configure_logging
from services.auth_service import auth_service
from utils.streamlit_auth import get_db_session, init_app_state, login_user, render_sidebar

configure_logging()
logger = logging.getLogger(__name__)

init_app_state()
render_sidebar()

st.title("📝 Register")

if st.session_state.get("logged_in"):
    st.info("You are already logged in.")
    st.stop()

with st.form("register_form"):
    username = st.text_input("Username", help="3-30 chars, letters, numbers, underscore")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password", help="Minimum 8 characters")
    confirm = st.text_input("Confirm Password", type="password")
    submitted = st.form_submit_button("Register", type="primary")

if submitted:
    db = get_db_session()
    try:
        ok, msg, user = auth_service.register(
            db, username, email, password, confirm
        )
        if ok and user:
            login_user(user)
            st.success(msg)
            st.switch_page("pages/3_resume.py")
        else:
            st.error(msg)
    except Exception as exc:
        logger.exception("Register page error: %s", exc)
        st.error(f"Registration failed: {exc}")
    finally:
        db.close()

st.page_link("pages/1_login.py", label="Already have an account? Login")
