"""Interview feedback review page."""

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
from utils.streamlit_auth import get_db_session, render_sidebar, require_login

configure_logging()
logger = logging.getLogger(__name__)

require_login()
render_sidebar()

st.title("💬 Interview Feedback")

db = get_db_session()
try:
    sessions = crud.get_user_sessions(db, st.session_state.user_id, limit=50)
    completed = [s for s in sessions if s.status == "completed"]

    if not completed:
        st.info("No completed interviews yet. Finish an interview to see feedback.")
        st.page_link("pages/4_interview.py", label="Start Interview")
        st.stop()

    session_options = {
        f"#{s.id} — {s.interview_type} ({s.avg_score:.1f}/10) — {s.started_at.strftime('%Y-%m-%d')}": s.id
        for s in completed
    }

    default_id = st.session_state.get("feedback_session_id")
    default_index = 0
    if default_id:
        for i, (_, sid) in enumerate(session_options.items()):
            if sid == default_id:
                default_index = i
                break

    selected_label = st.selectbox(
        "Select Interview Session",
        list(session_options.keys()),
        index=default_index,
    )
    session_id = session_options[selected_label]

    session = crud.get_interview_session(db, session_id)
    if not session:
        st.error("Session not found.")
        st.stop()

    st.subheader(f"{session.interview_type}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average Score", f"{session.avg_score:.2f}")
    c2.metric("Total Score", f"{session.total_score:.1f}")
    c3.metric("Difficulty", session.difficulty.capitalize())
    c4.metric("Status", session.status.capitalize())

    pairs = crud.get_session_qa_pairs(db, session_id)

    for question, answer in pairs:
        with st.container(border=True):
            st.markdown(f"### Question {question.question_number}")
            st.markdown(f"**{question.question_text}**")
            st.caption(
                f"Difficulty: {question.difficulty} | Topic: {question.topic or 'general'}"
            )

            if answer:
                st.markdown("**Your Answer:**")
                st.write(answer.answer_text)
                st.metric("Score", f"{answer.score:.1f} / 10")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Strengths**")
                    st.markdown(answer.strengths or "_None_")
                with col2:
                    st.markdown("**Weaknesses**")
                    st.markdown(answer.weaknesses or "_None_")

                st.markdown("**Missing Concepts**")
                st.markdown(answer.missing_concepts or "_None_")

                st.markdown("**Improved Answer**")
                st.success(answer.improved_answer or "N/A")

                if answer.follow_up_question:
                    st.markdown("**Suggested Follow-up**")
                    st.info(answer.follow_up_question)
            else:
                st.warning("No answer recorded for this question.")

    st.page_link("pages/7_report.py", label="Download PDF Report", icon="📥")

finally:
    db.close()
