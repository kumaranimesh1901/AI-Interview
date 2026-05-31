"""CRUD operations for all database entities."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.interview import InterviewAnswer, InterviewQuestion, InterviewSession
from models.resume import Resume, ResumeEducation, ResumeProject, ResumeSkill
from models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def create_user(
    db: Session,
    username: str,
    email: str,
    password_hash: str,
) -> Optional[User]:
    """Create a new user record."""
    try:
        user = User(
            username=username.strip().lower(),
            email=email.strip().lower(),
            password_hash=password_hash,
        )
        db.add(user)
        db.flush()
        db.refresh(user)
        return user
    except Exception as exc:
        logger.exception("create_user failed: %s", exc)
        raise


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Fetch user by username."""
    try:
        return (
            db.query(User)
            .filter(User.username == username.strip().lower())
            .first()
        )
    except Exception as exc:
        logger.exception("get_user_by_username failed: %s", exc)
        raise


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch user by email."""
    try:
        return (
            db.query(User)
            .filter(User.email == email.strip().lower())
            .first()
        )
    except Exception as exc:
        logger.exception("get_user_by_email failed: %s", exc)
        raise


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Fetch user by primary key."""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as exc:
        logger.exception("get_user_by_id failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------


def create_resume(
    db: Session,
    user_id: int,
    filename: str,
    raw_text: str,
) -> Optional[Resume]:
    """Store uploaded resume."""
    try:
        resume = Resume(user_id=user_id, filename=filename, raw_text=raw_text)
        db.add(resume)
        db.flush()
        db.refresh(resume)
        return resume
    except Exception as exc:
        logger.exception("create_resume failed: %s", exc)
        raise


def get_latest_resume(db: Session, user_id: int) -> Optional[Resume]:
    """Get most recent resume for user with relations."""
    try:
        return (
            db.query(Resume)
            .options(
                joinedload(Resume.skills),
                joinedload(Resume.projects),
                joinedload(Resume.education),
            )
            .filter(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
    except Exception as exc:
        logger.exception("get_latest_resume failed: %s", exc)
        raise


def add_resume_skills(
    db: Session,
    resume_id: int,
    skills: List[Dict[str, str]],
) -> None:
    """Bulk insert resume skills."""
    try:
        for item in skills:
            db.add(
                ResumeSkill(
                    resume_id=resume_id,
                    skill_name=item.get("skill_name", ""),
                    category=item.get("category", "general"),
                )
            )
        db.flush()
    except Exception as exc:
        logger.exception("add_resume_skills failed: %s", exc)
        raise


def add_resume_projects(
    db: Session,
    resume_id: int,
    projects: List[Dict[str, str]],
) -> None:
    """Bulk insert resume projects."""
    try:
        for item in projects:
            db.add(
                ResumeProject(
                    resume_id=resume_id,
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    technologies=item.get("technologies", ""),
                )
            )
        db.flush()
    except Exception as exc:
        logger.exception("add_resume_projects failed: %s", exc)
        raise


def add_resume_education(
    db: Session,
    resume_id: int,
    education: List[Dict[str, str]],
) -> None:
    """Bulk insert resume education entries."""
    try:
        for item in education:
            db.add(
                ResumeEducation(
                    resume_id=resume_id,
                    degree=item.get("degree", ""),
                    institution=item.get("institution", ""),
                    year=item.get("year", ""),
                )
            )
        db.flush()
    except Exception as exc:
        logger.exception("add_resume_education failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Interview sessions
# ---------------------------------------------------------------------------


def create_interview_session(
    db: Session,
    user_id: int,
    interview_type: str,
    difficulty: str,
) -> Optional[InterviewSession]:
    """Start a new interview session."""
    try:
        session = InterviewSession(
            user_id=user_id,
            interview_type=interview_type,
            difficulty=difficulty,
            status="in_progress",
        )
        db.add(session)
        db.flush()
        db.refresh(session)
        return session
    except Exception as exc:
        logger.exception("create_interview_session failed: %s", exc)
        raise


def get_interview_session(
    db: Session,
    session_id: int,
) -> Optional[InterviewSession]:
    """Get session with questions and answers."""
    try:
        return (
            db.query(InterviewSession)
            .options(
                joinedload(InterviewSession.questions).joinedload(
                    InterviewQuestion.answers
                ),
                joinedload(InterviewSession.answers),
            )
            .filter(InterviewSession.id == session_id)
            .first()
        )
    except Exception as exc:
        logger.exception("get_interview_session failed: %s", exc)
        raise


def update_session_difficulty(
    db: Session,
    session_id: int,
    difficulty: str,
) -> None:
    """Update current difficulty for adaptive engine."""
    try:
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()
        if session:
            session.difficulty = difficulty
            db.flush()
    except Exception as exc:
        logger.exception("update_session_difficulty failed: %s", exc)
        raise


def complete_interview_session(
    db: Session,
    session_id: int,
    total_score: float,
    avg_score: float,
) -> None:
    """Mark session completed with final scores."""
    try:
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).first()
        if session:
            session.status = "completed"
            session.total_score = total_score
            session.avg_score = avg_score
            session.completed_at = datetime.utcnow()
            db.flush()
    except Exception as exc:
        logger.exception("complete_interview_session failed: %s", exc)
        raise


def get_user_sessions(
    db: Session,
    user_id: int,
    limit: Optional[int] = None,
) -> List[InterviewSession]:
    """List interview sessions for a user."""
    try:
        q = (
            db.query(InterviewSession)
            .filter(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
        )
        if limit:
            q = q.limit(limit)
        return list(q.all())
    except Exception as exc:
        logger.exception("get_user_sessions failed: %s", exc)
        raise


def create_question(
    db: Session,
    session_id: int,
    question_text: str,
    question_number: int,
    difficulty: str,
    topic: str,
) -> Optional[InterviewQuestion]:
    """Persist an interview question."""
    try:
        question = InterviewQuestion(
            session_id=session_id,
            question_text=question_text,
            question_number=question_number,
            difficulty=difficulty,
            topic=topic,
        )
        db.add(question)
        db.flush()
        db.refresh(question)
        return question
    except Exception as exc:
        logger.exception("create_question failed: %s", exc)
        raise


def create_answer(
    db: Session,
    question_id: int,
    session_id: int,
    answer_text: str,
    score: float,
    strengths: str,
    weaknesses: str,
    missing_concepts: str,
    improved_answer: str,
    follow_up_question: str = "",
) -> Optional[InterviewAnswer]:
    """Persist evaluated answer."""
    try:
        answer = InterviewAnswer(
            question_id=question_id,
            session_id=session_id,
            answer_text=answer_text,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_concepts=missing_concepts,
            improved_answer=improved_answer,
            follow_up_question=follow_up_question,
        )
        db.add(answer)
        db.flush()
        db.refresh(answer)
        return answer
    except Exception as exc:
        logger.exception("create_answer failed: %s", exc)
        raise


def get_session_qa_pairs(
    db: Session,
    session_id: int,
) -> List[Tuple[InterviewQuestion, Optional[InterviewAnswer]]]:
    """Return ordered question-answer pairs for a session."""
    try:
        questions = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.question_number)
            .all()
        )
        pairs: List[Tuple[InterviewQuestion, Optional[InterviewAnswer]]] = []
        for q in questions:
            answer = (
                db.query(InterviewAnswer)
                .filter(InterviewAnswer.question_id == q.id)
                .first()
            )
            pairs.append((q, answer))
        return pairs
    except Exception as exc:
        logger.exception("get_session_qa_pairs failed: %s", exc)
        raise


def get_analytics_aggregates(db: Session, user_id: int) -> Dict[str, Any]:
    """Compute aggregate stats for analytics."""
    try:
        completed = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "completed",
            )
            .all()
        )
        total = len(completed)
        avg_all = (
            sum(s.avg_score for s in completed) / total if total > 0 else 0.0
        )

        by_type: Dict[str, List[float]] = {}
        for s in completed:
            by_type.setdefault(s.interview_type, []).append(s.avg_score)

        scores_by_type = {
            t: sum(scores) / len(scores) for t, scores in by_type.items()
        }

        topic_rows = (
            db.query(
                InterviewQuestion.topic,
                func.avg(InterviewAnswer.score).label("avg_score"),
                func.count(InterviewAnswer.id).label("cnt"),
            )
            .join(InterviewAnswer, InterviewAnswer.question_id == InterviewQuestion.id)
            .join(InterviewSession, InterviewSession.id == InterviewQuestion.session_id)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewQuestion.topic.isnot(None),
            )
            .group_by(InterviewQuestion.topic)
            .all()
        )

        return {
            "total_interviews": total,
            "average_score": round(avg_all, 2),
            "scores_by_type": scores_by_type,
            "topic_rows": topic_rows,
            "sessions": completed,
        }
    except Exception as exc:
        logger.exception("get_analytics_aggregates failed: %s", exc)
        raise
