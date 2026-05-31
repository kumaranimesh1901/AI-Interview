"""Resume and related ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

if TYPE_CHECKING:
    from models.user import User


class Resume(Base):
    """Uploaded resume document for a user."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="resumes")
    skills: Mapped[List["ResumeSkill"]] = relationship(
        "ResumeSkill",
        back_populates="resume",
        cascade="all, delete-orphan",
    )
    projects: Mapped[List["ResumeProject"]] = relationship(
        "ResumeProject",
        back_populates="resume",
        cascade="all, delete-orphan",
    )
    education: Mapped[List["ResumeEducation"]] = relationship(
        "ResumeEducation",
        back_populates="resume",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Resume id={self.id} user_id={self.user_id}>"


class ResumeSkill(Base):
    """Skill extracted from a resume."""

    __tablename__ = "resume_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="skills")

    def __repr__(self) -> str:
        return f"<ResumeSkill {self.skill_name!r}>"


class ResumeProject(Base):
    """Project extracted from a resume."""

    __tablename__ = "resume_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    technologies: Mapped[str] = mapped_column(String(500), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="projects")

    def __repr__(self) -> str:
        return f"<ResumeProject {self.title!r}>"


class ResumeEducation(Base):
    """Education entry extracted from a resume."""

    __tablename__ = "resume_education"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    degree: Mapped[str] = mapped_column(String(200), nullable=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=True)
    year: Mapped[str] = mapped_column(String(20), nullable=True)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="education")

    def __repr__(self) -> str:
        return f"<ResumeEducation {self.degree!r}>"
