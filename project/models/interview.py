"""Interview session, question, and answer ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

if TYPE_CHECKING:
    from models.user import User


class InterviewSession(Base):
    """A single interview practice session."""

    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    interview_type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")

    user: Mapped["User"] = relationship("User", back_populates="interview_sessions")
    questions: Mapped[List["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    answers: Mapped[List["InterviewAnswer"]] = relationship(
        "InterviewAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InterviewSession id={self.id} type={self.interview_type!r}>"


class InterviewQuestion(Base):
    """Question asked during an interview session."""

    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="questions",
    )
    answers: Mapped[List["InterviewAnswer"]] = relationship(
        "InterviewAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<InterviewQuestion #{self.question_number} session={self.session_id}>"


class InterviewAnswer(Base):
    """User answer with AI evaluation metadata."""

    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    strengths: Mapped[str] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str] = mapped_column(Text, nullable=True)
    missing_concepts: Mapped[str] = mapped_column(Text, nullable=True)
    improved_answer: Mapped[str] = mapped_column(Text, nullable=True)
    follow_up_question: Mapped[str] = mapped_column(Text, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    question: Mapped["InterviewQuestion"] = relationship(
        "InterviewQuestion",
        back_populates="answers",
    )
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="answers",
    )

    def __repr__(self) -> str:
        return f"<InterviewAnswer id={self.id} score={self.score}>"
