"""PDF report generation service facade."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database import crud
from models.user import User
from reports.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ReportService:
    """Builds downloadable interview PDF reports."""

    def __init__(self) -> None:
        """Initialize report generator."""
        self.generator = ReportGenerator()

    def build_session_report(
        self,
        db: Session,
        user: User,
        session_id: int,
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Generate PDF for a completed interview session.

        Returns:
            Tuple of (success, message, file_path).
        """
        try:
            session = crud.get_interview_session(db, session_id)
            if not session:
                return False, "Session not found.", None
            if session.user_id != user.id:
                return False, "Unauthorized access to session.", None

            pairs = crud.get_session_qa_pairs(db, session_id)
            qa_data: List[Dict[str, Any]] = []
            for question, answer in pairs:
                qa_data.append(
                    {
                        "question_number": question.question_number,
                        "question": question.question_text,
                        "difficulty": question.difficulty,
                        "topic": question.topic or "",
                        "answer": answer.answer_text if answer else "No answer",
                        "score": answer.score if answer else 0.0,
                        "strengths": answer.strengths if answer else "",
                        "weaknesses": answer.weaknesses if answer else "",
                        "missing_concepts": answer.missing_concepts if answer else "",
                        "improved_answer": answer.improved_answer if answer else "",
                    }
                )

            report_data = {
                "username": user.username,
                "email": user.email,
                "interview_type": session.interview_type,
                "difficulty": session.difficulty,
                "status": session.status,
                "total_score": session.total_score,
                "avg_score": session.avg_score,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "qa_pairs": qa_data,
            }

            path = self.generator.generate(report_data, session_id)
            return True, "Report generated.", path
        except Exception as exc:
            logger.exception("build_session_report failed: %s", exc)
            return False, f"Report generation failed: {exc}", None


report_service = ReportService()
