"""Adaptive interview session page."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import configure_logging, settings
from services.interview_service import (
    DIFFICULTY_LEVELS,
    INTERVIEW_TYPES,
    interview_service,
)
from utils.streamlit_auth import get_db_session, render_sidebar, require_login

configure_logging()
logger = logging.getLogger(__name__)

require_login()
render_sidebar()

st.title("🎤 Adaptive Interview")
st.markdown(
    f"Answer **{settings.QUESTIONS_PER_SESSION}** questions. "
    f"Difficulty adapts: increases above {settings.SCORE_INCREASE_THRESHOLD}/10, "
    f"decreases below {settings.SCORE_DECREASE_THRESHOLD}/10."
)

# --- Start new session ---
if not st.session_state.get("interview_session_id"):
    st.subheader("Start New Session")
    col1, col2 = st.columns(2)
    with col1:
        interview_type = st.selectbox("Interview Type", INTERVIEW_TYPES)
    with col2:
        difficulty = st.selectbox(
            "Starting Difficulty",
            DIFFICULTY_LEVELS,
            format_func=lambda x: x.capitalize(),
        )

    if st.button("Start Interview", type="primary"):
        db = get_db_session()
        try:
            ok, msg, session = interview_service.start_session(
                db,
                user_id=st.session_state.user_id,
                interview_type=interview_type,
                difficulty=difficulty,
            )
            if ok and session:
                st.session_state.interview_session_id = session.id
                st.session_state.current_question_number = 0
                st.session_state.interview_answers_count = 0
                st.session_state.current_question_id = None
                st.session_state.last_evaluation = None
                st.success("Interview started!")
                st.rerun()
            else:
                st.error(msg)
        except Exception as exc:
            logger.exception("Start interview error: %s", exc)
            st.error(str(exc))
        finally:
            db.close()
    st.stop()

# --- Active session ---
session_id: int = st.session_state.interview_session_id
db = get_db_session()

try:
    session = interview_service.get_session_state(db, session_id)
    if not session:
        st.error("Session not found. Start a new interview.")
        st.session_state.interview_session_id = None
        st.stop()

    # Session already completed
    if session.status == "completed":
        st.success("This interview session is complete.")
        st.metric("Average Score", f"{session.avg_score:.2f} / 10")
        if st.button("View Feedback"):
            st.session_state.feedback_session_id = session_id
            st.switch_page("pages/5_feedback.py")
        if st.button("Start New Interview"):
            st.session_state.interview_session_id = None
            st.rerun()
        st.stop()

    # Count answered questions
    answers_count = len(list(session.answers))
    q_number = answers_count + 1

    st.progress(
        min(answers_count / settings.QUESTIONS_PER_SESSION, 1.0),
        text=f"Question {min(q_number, settings.QUESTIONS_PER_SESSION)} of {settings.QUESTIONS_PER_SESSION}",
    )

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Type", session.interview_type)
    col_b.metric("Difficulty", session.difficulty.capitalize())
    col_c.metric("Answered", answers_count)

    # Show last evaluation if pending display
    if st.session_state.get("last_evaluation"):
        ev = st.session_state.last_evaluation
        with st.expander("Previous Answer Feedback", expanded=True):
            st.metric("Score", f"{ev.get('score', 0):.1f} / 10")
            st.markdown(f"**Strengths:**\n{ev.get('strengths', '')}")
            st.markdown(f"**Weaknesses:**\n{ev.get('weaknesses', '')}")
            st.markdown(f"**Missing Concepts:**\n{ev.get('missing_concepts', '')}")
            st.markdown(f"**Improved Answer:**\n{ev.get('improved_answer', '')}")
            if ev.get("follow_up_question"):
                st.info(f"Follow-up: {ev.get('follow_up_question')}")
            if ev.get("new_difficulty"):
                st.caption(f"Next question difficulty: **{ev['new_difficulty'].capitalize()}**")
        if st.button("Continue to Next Question"):
            st.session_state.last_evaluation = None
            st.rerun()
        # Don't show the question form while evaluation is displayed
        st.stop()

    # Check if session should be finalized
    if answers_count >= settings.QUESTIONS_PER_SESSION:
        ok, msg, total, avg = interview_service.finalize_session(db, session_id)
        if ok:
            st.success(f"Interview complete! Average score: {avg:.2f}/10")
            st.session_state.feedback_session_id = session_id
            st.balloons()
            col_fb, col_new = st.columns(2)
            with col_fb:
                if st.button("View Full Feedback"):
                    st.switch_page("pages/5_feedback.py")
            with col_new:
                if st.button("Start New Interview"):
                    st.session_state.interview_session_id = None
                    st.rerun()
        else:
            st.error(msg)
        st.stop()

    # Find unanswered question or generate new one
    current_q = None
    for q in sorted(session.questions, key=lambda x: x.question_number):
        has_answer = any(a.question_id == q.id for a in session.answers)
        if not has_answer:
            current_q = q
            break

    if current_q is None:
        with st.spinner("Generating question..."):
            ok, msg, current_q = interview_service.generate_question(
                db,
                session=session,
                question_number=q_number,
                model=st.session_state.get("groq_model"),
            )
        if not ok or not current_q:
            st.error(f"Failed to generate question: {msg}")
            st.stop()
        # Refresh session state after generating question
        session = interview_service.get_session_state(db, session_id)

    if current_q:
        st.subheader(f"Question {current_q.question_number}")
        st.info(current_q.question_text)
        st.caption(f"Topic: {current_q.topic} | Difficulty: {current_q.difficulty}")

        with st.form("answer_form"):
            answer = st.text_area(
                "Your Answer",
                height=200,
                placeholder="Type your detailed answer here...",
            )
            submit = st.form_submit_button("Submit Answer", type="primary")

        if submit:
            if not answer or not answer.strip():
                st.warning("Please provide an answer.")
            else:
                with st.spinner("Evaluating your answer with AI..."):
                    ok, msg, evaluation = interview_service.submit_answer(
                        db,
                        session=session,
                        question=current_q,
                        answer_text=answer.strip(),
                        model=st.session_state.get("groq_model"),
                    )
                if ok:
                    st.session_state.last_evaluation = evaluation
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.warning("Could not load question. Try refreshing.")

    if st.button("Abandon Session", type="secondary"):
        st.session_state.interview_session_id = None
        st.session_state.last_evaluation = None
        st.rerun()

finally:
    db.close()
