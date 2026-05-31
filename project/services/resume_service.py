"""Resume PDF parsing and AI-powered extraction."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from database import crud
from models.resume import Resume
from prompts.resume_prompts import resume_extraction_prompt
from services.llm_service import LLMService, llm_service
from utils.helpers import parse_json_from_llm

logger = logging.getLogger(__name__)


class ResumeService:
    """Handles PDF upload, text extraction, and structured parsing."""

    def __init__(self, llm: Optional[LLMService] = None) -> None:
        """Initialize with optional custom LLM client."""
        self.llm = llm or llm_service

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> Tuple[bool, str, str]:
        """
        Extract raw text from PDF bytes.

        Returns:
            Tuple of (success, text_or_error, message).
        """
        try:
            reader = PdfReader(BytesIO(file_bytes))
            pages: List[str] = []
            for page in reader.pages:
                try:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                except Exception as page_exc:
                    logger.warning("Page extract failed: %s", page_exc)
            full_text = "\n".join(pages).strip()
            if not full_text:
                return False, "", "Could not extract text from PDF. It may be scanned/image-only."
            return True, full_text, "Text extracted successfully."
        except Exception as exc:
            logger.exception("extract_text_from_pdf failed: %s", exc)
            return False, "", f"PDF parsing error: {exc}"

    def parse_resume_with_llm(self, raw_text: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Use LLM to extract structured resume data.

        Returns:
            Parsed dict with skills, projects, education, experience_summary.
        """
        default: Dict[str, Any] = {
            "skills": [],
            "projects": [],
            "education": [],
            "experience_summary": "",
        }
        try:
            prompt = resume_extraction_prompt(raw_text)
            response = self.llm.generate(
                prompt,
                system="You are a precise JSON-only resume parser.",
                model=model,
                temperature=0.2,
            )
            parsed = parse_json_from_llm(response)
            if not parsed:
                logger.warning("LLM resume parse returned no JSON; using fallback")
                return self._fallback_parse(raw_text)

            return {
                "skills": parsed.get("skills", []) or [],
                "projects": parsed.get("projects", []) or [],
                "education": parsed.get("education", []) or [],
                "experience_summary": parsed.get("experience_summary", "") or "",
            }
        except Exception as exc:
            logger.exception("parse_resume_with_llm failed: %s", exc)
            return self._fallback_parse(raw_text)

    @staticmethod
    def _fallback_parse(raw_text: str) -> Dict[str, Any]:
        """Basic heuristic extraction when LLM fails."""
        try:
            lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]
            skills_keywords = [
                "python", "java", "javascript", "sql", "react", "docker",
                "kubernetes", "aws", "machine learning", "tensorflow",
            ]
            found_skills = []
            lower_text = raw_text.lower()
            for kw in skills_keywords:
                if kw in lower_text:
                    found_skills.append({"skill_name": kw.title(), "category": "detected"})

            return {
                "skills": found_skills[:20],
                "projects": [],
                "education": [],
                "experience_summary": "\n".join(lines[:15])[:500],
            }
        except Exception as exc:
            logger.exception("_fallback_parse failed: %s", exc)
            return {
                "skills": [],
                "projects": [],
                "education": [],
                "experience_summary": raw_text[:500] if raw_text else "",
            }

    def process_upload(
        self,
        db: Session,
        user_id: int,
        filename: str,
        file_bytes: bytes,
        model: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Resume]]:
        """
        Full pipeline: extract PDF, parse, persist.

        Returns:
            Tuple of (success, message, resume).
        """
        try:
            ok, raw_text, msg = self.extract_text_from_pdf(file_bytes)
            if not ok:
                return False, msg, None

            parsed = self.parse_resume_with_llm(raw_text, model=model)
            resume = crud.create_resume(db, user_id, filename, raw_text)
            if not resume:
                return False, "Failed to save resume.", None

            crud.add_resume_skills(db, resume.id, parsed.get("skills", []))
            crud.add_resume_projects(db, resume.id, parsed.get("projects", []))
            crud.add_resume_education(db, resume.id, parsed.get("education", []))
            db.commit()

            refreshed = crud.get_latest_resume(db, user_id)
            return True, "Resume uploaded and analyzed successfully.", refreshed
        except Exception as exc:
            db.rollback()
            logger.exception("process_upload failed: %s", exc)
            return False, f"Resume processing failed: {exc}", None

    def get_resume_context(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Build resume context dict for interview personalization."""
        try:
            resume = crud.get_latest_resume(db, user_id)
            if not resume:
                return {
                    "skills": [],
                    "projects": [],
                    "education": [],
                    "experience_summary": "",
                    "raw_text": "",
                }
            return {
                "skills": [s.skill_name for s in resume.skills],
                "projects": [
                    {
                        "title": p.title,
                        "description": p.description or "",
                        "technologies": p.technologies or "",
                    }
                    for p in resume.projects
                ],
                "education": [
                    {
                        "degree": e.degree or "",
                        "institution": e.institution or "",
                        "year": e.year or "",
                    }
                    for e in resume.education
                ],
                "experience_summary": resume.raw_text[:800],
                "raw_text": resume.raw_text,
            }
        except Exception as exc:
            logger.exception("get_resume_context failed: %s", exc)
            return {
                "skills": [],
                "projects": [],
                "education": [],
                "experience_summary": "",
                "raw_text": "",
            }


resume_service = ResumeService()
