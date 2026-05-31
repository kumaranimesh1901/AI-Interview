"""Prompt templates for interview question generation."""

from __future__ import annotations

from typing import Optional


INTERVIEW_TYPE_DESCRIPTIONS: dict[str, str] = {
    "Technical Interview": "core programming, software engineering, debugging, APIs, databases",
    "HR Interview": "behavioral questions, teamwork, conflict resolution, career goals, culture fit",
    "DSA Interview": "data structures, algorithms, time/space complexity, problem-solving patterns",
    "Machine Learning Interview": "ML fundamentals, model training, evaluation, feature engineering, deployment",
    "System Design Interview": "scalability, distributed systems, trade-offs, architecture diagrams verbally",
}


def initial_question_prompt(
    interview_type: str,
    difficulty: str,
    question_number: int,
    resume_context: str,
    previous_qa: str = "",
) -> str:
    """
    Generate prompt for a new interview question.

    Args:
        interview_type: Type of interview session.
        difficulty: easy, medium, or hard.
        question_number: Current question index (1-10).
        resume_context: Personalized context from resume.
        previous_qa: Summary of prior Q&A in this session.

    Returns:
        Formatted prompt string.
    """
    type_focus = INTERVIEW_TYPE_DESCRIPTIONS.get(
        interview_type,
        "general technical interview skills",
    )
    prev_block = ""
    if previous_qa:
        prev_block = f"""
Previous questions and answers in this session (use for context-aware follow-ups):
{previous_qa}
"""

    return f"""You are a senior interviewer conducting a {interview_type}.
Focus areas: {type_focus}.

Generate question #{question_number} of 10 for a candidate.
Difficulty level: {difficulty.upper()}.

Candidate background from resume:
{resume_context}
{prev_block}

Requirements:
- Ask ONE clear, specific question appropriate for {difficulty} difficulty
- Personalize using resume skills/projects when relevant
- For question 2+, you may ask a follow-up that builds on prior answers
- Do not repeat questions already asked

Return ONLY valid JSON:
{{
  "question": "The interview question text",
  "topic": "short topic label e.g. arrays, leadership, caching"
}}
"""


def follow_up_question_prompt(
    interview_type: str,
    difficulty: str,
    original_question: str,
    candidate_answer: str,
    evaluation_summary: str,
) -> str:
    """
    Generate a contextual follow-up question based on the answer.

    Args:
        interview_type: Session interview type.
        difficulty: Current difficulty level.
        original_question: The question that was answered.
        candidate_answer: User's answer text.
        evaluation_summary: Brief evaluation notes.

    Returns:
        Formatted prompt string.
    """
    return f"""You are conducting a {interview_type} at {difficulty} difficulty.

Original question: {original_question}

Candidate answer: {candidate_answer}

Evaluation notes: {evaluation_summary}

Generate ONE sharp follow-up question that probes gaps or deeper understanding.
Return ONLY valid JSON:
{{
  "follow_up_question": "The follow-up question text"
}}
"""
