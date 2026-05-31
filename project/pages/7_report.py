"""PDF report download page."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import configure_logging
from database import crud
from services.auth_service import auth_service
from services.report_service import report_service
from utils.streamlit_auth import get_db_session, render_sidebar, require_login

configure_logging()
logger = logging.getLogger(__name__)

require_login()
render_sidebar()

st.title("📥 PDF Interview Report")
st.markdown("Generate a comprehensive PDF report for any completed interview session.")

db = get_db_session()
try:
    user = auth_service.get_user(db, st.session_state.user_id)
    if not user:
        st.error("User not found.")
        st.stop()

    sessions = crud.get_user_sessions(db, st.session_state.user_id, limit=50)
    completed = [s for s in sessions if s.status == "completed"]

    if not completed:
        st.info("No completed interviews available for reporting.")
        st.page_link("pages/4_interview.py", label="Start an Interview")
        st.stop()

    session_options = {
        f"#{s.id} — {s.interview_type} (Avg: {s.avg_score:.1f})": s.id
        for s in completed
    }

    default_id = st.session_state.get("feedback_session_id")
    default_index = 0
    if default_id:
        for i, (_, sid) in enumerate(session_options.items()):
            if sid == default_id:
                default_index = i
                break

    selected = st.selectbox(
        "Select Session",
        list(session_options.keys()),
        index=default_index,
    )
    session_id = session_options[selected]

    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Building PDF report..."):
            ok, msg, path = report_service.build_session_report(db, user, session_id)
        if ok and path and path.exists():
            st.success(msg)
            with open(path, "rb") as pdf_file:
                st.download_button(
                    label="Download PDF",
                    data=pdf_file.read(),
                    file_name=path.name,
                    mime="application/pdf",
                    type="primary",
                )
            st.caption(f"Saved to: {path}")
        else:
            st.error(msg)

    st.divider()
    st.markdown("### Report Contents")
    st.markdown(
        """
- Candidate information
- Interview type and difficulty
- All questions and answers
- Per-question scores and feedback
- Strengths, weaknesses, missing concepts
- Model improved answers
- Overall performance summary
        """
    )

except Exception as exc:
    logger.exception("Report page error: %s", exc)
    st.error(f"Report error: {exc}")
finally:
    db.close()
