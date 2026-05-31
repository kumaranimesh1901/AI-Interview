"""Login page."""

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

st.title("🔐 Login")

if st.session_state.get("logged_in"):
    st.success(f"Already logged in as {st.session_state.username}")
    st.page_link("app.py", label="Go to Home")
    st.page_link("pages/4_interview.py", label="Start Interview")
    st.stop()

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", type="primary")

if submitted:
    db = get_db_session()
    try:
        ok, msg, user = auth_service.login(db, username, password)
        if ok and user:
            login_user(user)
            st.success(msg)
            st.balloons()
            st.switch_page("app.py")
        else:
            st.error(msg)
    except Exception as exc:
        logger.exception("Login page error: %s", exc)
        st.error(f"Login failed: {exc}")
    finally:
        db.close()

st.page_link("pages/2_register.py", label="Create an account")
