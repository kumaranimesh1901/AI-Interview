"""Prompt templates for answer evaluation."""

from __future__ import annotations


def answer_evaluation_prompt(
    interview_type: str,
    question: str,
    answer: str,
    difficulty: str,
    topic: str,
) -> str:
    """
    Build prompt to evaluate a candidate's interview answer.

    Args:
        interview_type: Type of interview.
        question: The interview question.
        answer: Candidate's answer.
        difficulty: Question difficulty level.
        topic: Question topic label.

    Returns:
        Formatted evaluation prompt.
    """
    return f"""You are an expert interview evaluator for {interview_type}.

Evaluate the candidate's answer rigorously but fairly.

Question ({difficulty}, topic: {topic}):
{question}

Candidate answer:
{answer}

Return ONLY valid JSON with this structure:
{{
  "score": 7.5,
  "strengths": ["point 1", "point 2"],
  "weaknesses": ["point 1", "point 2"],
  "missing_concepts": ["concept 1", "concept 2"],
  "improved_answer": "A concise model answer demonstrating best practices (3-6 sentences)",
  "follow_up_question": "One follow-up question based on gaps in the answer"
}}

Scoring guide (0-10):
- 0-3: Incorrect or irrelevant
- 4-5: Partial understanding, major gaps
- 6-7: Adequate with notable gaps
- 8-9: Strong, minor improvements possible
- 10: Exceptional, comprehensive

Be specific in strengths, weaknesses, and missing_concepts.
"""
