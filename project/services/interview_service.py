"""Adaptive interview engine orchestration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import settings
from database import crud
from models.interview import InterviewQuestion, InterviewSession
from prompts.interview_prompts import initial_question_prompt
from services.evaluation_service import EvaluationService, evaluation_service
from services.ollama_service import OllamaService, ollama_service
from services.resume_service import ResumeService, resume_service
from utils.helpers import adjust_difficulty, parse_json_from_llm, resume_context_summary

logger = logging.getLogger(__name__)

INTERVIEW_TYPES: List[str] = [
    "Technical Interview",
    "HR Interview",
    "DSA Interview",
    "Machine Learning Interview",
    "System Design Interview",
]

DIFFICULTY_LEVELS: List[str] = ["easy", "medium", "hard"]


class InterviewService:
    """Manages interview sessions, question generation, and adaptive difficulty."""

    def __init__(
        self,
        llm: Optional[OllamaService] = None,
        evaluator: Optional[EvaluationService] = None,
        resume_svc: Optional[ResumeService] = None,
    ) -> None:
        """
        Initialize with optional dependency overrides.

        Args:
            llm: LLM client for question generation.
            evaluator: Answer evaluation service.
            resume_svc: Resume context provider.
        """
        self.llm = llm or ollama_service
        self.evaluator = evaluator or evaluation_service
        self.resume_svc = resume_svc or resume_service

    def start_session(
        self,
        db: Session,
        user_id: int,
        interview_type: str,
        difficulty: str,
    ) -> Tuple[bool, str, Optional[InterviewSession]]:
        """
        Create a new interview session.

        Args:
            db: Database session (caller manages commit/close).
            user_id: Current user's ID.
            interview_type: One of INTERVIEW_TYPES.
            difficulty: Starting difficulty level.

        Returns:
            Tuple of (success, message, session_or_none).
        """
        try:
            if interview_type not in INTERVIEW_TYPES:
                return False, "Invalid interview type.", None
            if difficulty.lower() not in DIFFICULTY_LEVELS:
                return False, "Invalid difficulty.", None

            session = crud.create_interview_session(
                db,
                user_id=user_id,
                interview_type=interview_type,
                difficulty=difficulty.lower(),
            )
            db.commit()
            return True, "Session started.", session
        except Exception as exc:
            db.rollback()
            logger.exception("start_session failed: %s", exc)
            return False, str(exc), None

    def _build_previous_qa_summary(
        self,
        db: Session,
        session_id: int,
    ) -> str:
        """
        Summarize prior Q&A for context-aware follow-up questions.

        Args:
            db: Database session.
            session_id: Current interview session ID.

        Returns:
            Formatted string of recent Q&A pairs (last 5).
        """
        try:
            pairs = crud.get_session_qa_pairs(db, session_id)
            lines: List[str] = []
            for q, a in pairs:
                if a:
                    lines.append(
                        f"Q{q.question_number}: {q.question_text[:200]}\n"
                        f"A: {a.answer_text[:300]} (score: {a.score})"
                    )
            return "\n\n".join(lines[-5:])
        except Exception as exc:
            logger.warning("_build_previous_qa_summary failed: %s", exc)
            return ""

    def generate_question(
        self,
        db: Session,
        session: InterviewSession,
        question_number: int,
        model: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[InterviewQuestion]]:
        """
        Generate and persist the next interview question using the LLM.

        Args:
            db: Database session.
            session: Current interview session.
            question_number: 1-based question index.
            model: Optional model override.

        Returns:
            Tuple of (success, message, question_or_none).
        """
        try:
            ctx = self.resume_svc.get_resume_context(db, session.user_id)
            resume_ctx = resume_context_summary(
                skills=ctx.get("skills", []),
                projects=ctx.get("projects", []),
                education=ctx.get("education", []),
                experience_snippet=ctx.get("experience_summary", ""),
            )
            previous_qa = self._build_previous_qa_summary(db, session.id)

            prompt = initial_question_prompt(
                interview_type=session.interview_type,
                difficulty=session.difficulty,
                question_number=question_number,
                resume_context=resume_ctx,
                previous_qa=previous_qa,
            )
            response = self.llm.generate(
                prompt,
                system="You are an expert interviewer. Return only JSON.",
                model=model,
                temperature=0.8,
            )
            parsed = parse_json_from_llm(response)
            if not parsed or not parsed.get("question"):
                # Fallback question if LLM fails to produce valid JSON
                question_text = (
                    f"[{session.interview_type}] Describe your experience with "
                    f"a key topic at {session.difficulty} level (Q{question_number})."
                )
                topic = "general"
                logger.warning(
                    "LLM question generation returned invalid JSON; using fallback. "
                    "Raw: %s",
                    response[:200],
                )
            else:
                question_text = str(parsed["question"])
                topic = str(parsed.get("topic", "general"))

            question = crud.create_question(
                db,
                session_id=session.id,
                question_text=question_text,
                question_number=question_number,
                difficulty=session.difficulty,
                topic=topic,
            )
            db.commit()
            return True, "Question generated.", question
        except Exception as exc:
            db.rollback()
            logger.exception("generate_question failed: %s", exc)
            return False, str(exc), None

    def submit_answer(
        self,
        db: Session,
        session: InterviewSession,
        question: InterviewQuestion,
        answer_text: str,
        model: Optional[str] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Evaluate an answer, persist it, and adjust session difficulty.

        Args:
            db: Database session.
            session: Current interview session.
            question: The question being answered.
            answer_text: User's answer text.
            model: Optional model override.

        Returns:
            Tuple of (success, message, evaluation_dict).
        """
        try:
            evaluation = self.evaluator.evaluate_answer(
                interview_type=session.interview_type,
                question=question.question_text,
                answer=answer_text,
                difficulty=question.difficulty,
                topic=question.topic or "general",
                model=model,
            )

            crud.create_answer(
                db,
                question_id=question.id,
                session_id=session.id,
                answer_text=answer_text,
                score=evaluation["score"],
                strengths=evaluation["strengths"],
                weaknesses=evaluation["weaknesses"],
                missing_concepts=evaluation["missing_concepts"],
                improved_answer=evaluation["improved_answer"],
                follow_up_question=evaluation.get("follow_up_question", ""),
            )

            # Adaptive difficulty adjustment
            new_difficulty = adjust_difficulty(
                session.difficulty,
                evaluation["score"],
                settings.SCORE_INCREASE_THRESHOLD,
                settings.SCORE_DECREASE_THRESHOLD,
            )
            if new_difficulty != session.difficulty:
                crud.update_session_difficulty(db, session.id, new_difficulty)
                session.difficulty = new_difficulty
                logger.info(
                    "Difficulty adjusted to %s for session %s (score: %s)",
                    new_difficulty,
                    session.id,
                    evaluation["score"],
                )

            db.commit()
            evaluation["new_difficulty"] = session.difficulty
            return True, "Answer evaluated.", evaluation
        except Exception as exc:
            db.rollback()
            logger.exception("submit_answer failed: %s", exc)
            return False, str(exc), {}

    def finalize_session(
        self,
        db: Session,
        session_id: int,
    ) -> Tuple[bool, str, float, float]:
        """
        Complete a session and compute aggregate scores.

        Args:
            db: Database session.
            session_id: Session to finalize.

        Returns:
            Tuple of (success, message, total_score, avg_score).
        """
        try:
            pairs = crud.get_session_qa_pairs(db, session_id)
            scores = [a.score for _, a in pairs if a is not None]
            total = sum(scores) if scores else 0.0
            avg = total / len(scores) if scores else 0.0
            crud.complete_interview_session(db, session_id, total, round(avg, 2))
            db.commit()
            return True, "Session completed.", total, round(avg, 2)
        except Exception as exc:
            db.rollback()
            logger.exception("finalize_session failed: %s", exc)
            return False, str(exc), 0.0, 0.0

    def get_session_state(
        self,
        db: Session,
        session_id: int,
    ) -> Optional[InterviewSession]:
        """
        Load full session with all relations (questions, answers).

        Args:
            db: Database session.
            session_id: Session ID to load.

        Returns:
            InterviewSession with eagerly loaded relations, or None.
        """
        try:
            return crud.get_interview_session(db, session_id)
        except Exception as exc:
            logger.exception("get_session_state failed: %s", exc)
            return None


interview_service = InterviewService()
