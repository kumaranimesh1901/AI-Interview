"""Resume upload and analysis page."""

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
from services.resume_service import resume_service
from utils.streamlit_auth import get_db_session, render_sidebar, require_login
from utils.validators import validate_pdf_filename

configure_logging()
logger = logging.getLogger(__name__)

require_login()
render_sidebar()

st.title("📄 Resume Analysis")
st.markdown("Upload your PDF resume for AI-powered extraction of skills, projects, and education.")

uploaded = st.file_uploader("Upload PDF Resume", type=["pdf"])

if uploaded is not None:
    ok, msg = validate_pdf_filename(uploaded.name)
    if not ok:
        st.error(msg)
    else:
        if st.button("Analyze Resume", type="primary"):
            db = get_db_session()
            try:
                with st.spinner("Extracting and analyzing resume with AI..."):
                    success, message, resume = resume_service.process_upload(
                        db,
                        user_id=st.session_state.user_id,
                        filename=uploaded.name,
                        file_bytes=uploaded.getvalue(),
                        model=st.session_state.get("ollama_model"),
                    )
                if success and resume:
                    st.success(message)
                    st.session_state.latest_resume_id = resume.id
                else:
                    st.error(message)
            except Exception as exc:
                logger.exception("Resume upload error: %s", exc)
                st.error(f"Upload failed: {exc}")
            finally:
                db.close()

# Display existing resume data
db = get_db_session()
try:
    full_resume = crud.get_latest_resume(db, st.session_state.user_id)

    if full_resume:
        st.subheader("Parsed Resume Data")
        st.caption(f"File: **{full_resume.filename}** | Uploaded: {full_resume.uploaded_at}")

        tab1, tab2, tab3, tab4 = st.tabs(["Skills", "Projects", "Education", "Raw Text"])

        with tab1:
            if full_resume.skills:
                skill_data = [
                    {"Skill": s.skill_name, "Category": s.category or "general"}
                    for s in full_resume.skills
                ]
                st.dataframe(skill_data, use_container_width=True)
            else:
                st.info("No skills extracted.")

        with tab2:
            if full_resume.projects:
                for p in full_resume.projects:
                    with st.expander(p.title):
                        st.write(p.description or "No description")
                        if p.technologies:
                            st.caption(f"Technologies: {p.technologies}")
            else:
                st.info("No projects extracted.")

        with tab3:
            if full_resume.education:
                edu_data = [
                    {
                        "Degree": e.degree,
                        "Institution": e.institution,
                        "Year": e.year,
                    }
                    for e in full_resume.education
                ]
                st.dataframe(edu_data, use_container_width=True)
            else:
                st.info("No education entries extracted.")

        with tab4:
            st.text_area(
                "Extracted Text",
                full_resume.raw_text[:8000],
                height=300,
                disabled=True,
            )
    else:
        st.warning("No resume uploaded yet. Upload a PDF to personalize your interviews.")
finally:
    db.close()
