"""Answer evaluation using LLM with structured feedback extraction."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from prompts.evaluation_prompts import answer_evaluation_prompt
from services.ollama_service import OllamaService, ollama_service
from utils.helpers import clamp_score, list_to_bullets, parse_json_from_llm

logger = logging.getLogger(__name__)


def _normalize_to_bullet_string(value: Any) -> str:
    """
    Convert a value (list or string) to a bullet-point string.

    LLMs may return either a list or a pre-formatted string for fields
    like strengths/weaknesses.  This normalizes both cases.

    Args:
        value: List of strings or a single string.

    Returns:
        Bullet-formatted string.
    """
    if isinstance(value, list):
        return list_to_bullets(value)
    if isinstance(value, str):
        return value.strip()
    return str(value) if value else ""


class EvaluationService:
    """Evaluates interview answers and returns structured feedback."""

    def __init__(self, llm: Optional[OllamaService] = None) -> None:
        """
        Initialize with optional LLM client.

        Args:
            llm: OllamaService instance (defaults to global singleton).
        """
        self.llm = llm or ollama_service

    def evaluate_answer(
        self,
        interview_type: str,
        question: str,
        answer: str,
        difficulty: str,
        topic: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a single interview answer using the LLM.

        Returns:
            Dict with keys: score (float), strengths (str), weaknesses (str),
            missing_concepts (str), improved_answer (str), follow_up_question (str).
        """
        default: Dict[str, Any] = {
            "score": 5.0,
            "strengths": "• Answer submitted for review.",
            "weaknesses": "• Could not complete AI evaluation.",
            "missing_concepts": "• Evaluation unavailable.",
            "improved_answer": "Please retry when Ollama is available.",
            "follow_up_question": "Can you elaborate on your approach?",
        }
        try:
            if not answer or not answer.strip():
                return {
                    "score": 0.0,
                    "strengths": "",
                    "weaknesses": "• No answer provided.",
                    "missing_concepts": "• Complete answer required.",
                    "improved_answer": "Provide a structured answer addressing the question directly.",
                    "follow_up_question": "What is your understanding of the core concept?",
                }

            prompt = answer_evaluation_prompt(
                interview_type=interview_type,
                question=question,
                answer=answer,
                difficulty=difficulty,
                topic=topic or "general",
            )
            response = self.llm.generate(
                prompt,
                system="You are a strict but fair technical interviewer. Return only JSON.",
                model=model,
                temperature=0.3,
            )
            parsed = parse_json_from_llm(response)
            if not parsed:
                logger.warning("Evaluation JSON parse failed; raw response: %s", response[:300])
                return default

            # Normalize list-or-string fields to bullet strings
            strengths = _normalize_to_bullet_string(parsed.get("strengths", []))
            weaknesses = _normalize_to_bullet_string(parsed.get("weaknesses", []))
            missing = _normalize_to_bullet_string(parsed.get("missing_concepts", []))

            return {
                "score": clamp_score(parsed.get("score", 5.0)),
                "strengths": strengths,
                "weaknesses": weaknesses,
                "missing_concepts": missing,
                "improved_answer": str(parsed.get("improved_answer", "")),
                "follow_up_question": str(
                    parsed.get("follow_up_question", "Can you go deeper on this topic?")
                ),
            }
        except Exception as exc:
            logger.exception("evaluate_answer failed: %s", exc)
            default["weaknesses"] = f"• Evaluation error: {exc}"
            return default


evaluation_service = EvaluationService()
