"""General helper utilities."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Pattern to strip <think>...</think> blocks produced by qwen3 and similar models.
_THINK_TAG_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)


def strip_thinking_tags(text: str) -> str:
    """
    Remove ``<think>...</think>`` blocks from LLM output.

    Many reasoning-oriented models (qwen3, deepseek-r1) wrap their chain-of-thought
    in ``<think>`` tags before emitting the real answer.  This function strips those
    blocks so downstream JSON / text parsing sees only the intended response.

    Args:
        text: Raw LLM output that may contain thinking tags.

    Returns:
        Cleaned text with thinking blocks removed and leading/trailing whitespace stripped.
    """
    if not text:
        return ""
    try:
        cleaned = _THINK_TAG_RE.sub("", text)
        return cleaned.strip()
    except Exception as exc:
        logger.warning("strip_thinking_tags failed: %s", exc)
        return text.strip()


def parse_json_from_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from LLM response text.

    Handles:
    - ``<think>`` blocks (stripped first)
    - Markdown code fences (``````json ... ``````)
    - Surrounding prose around a JSON object
    - Direct JSON strings

    Args:
        text: Raw LLM output potentially containing a JSON object.

    Returns:
        Parsed dictionary, or ``None`` if no valid JSON found.
    """
    if not text or not text.strip():
        return None
    try:
        # Strip thinking tags first (critical for qwen3)
        cleaned = strip_thinking_tags(text)
        if not cleaned:
            return None

        # Try direct parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Extract from ```json ... ``` or ``` ... ```
        fence_match = re.search(
            r"```(?:json)?\s*([\s\S]*?)\s*```",
            cleaned,
            re.IGNORECASE,
        )
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Find first balanced { ... } block using greedy match
        brace_match = re.search(r"\{[\s\S]*\}", cleaned)
        if brace_match:
            candidate = brace_match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Try to find innermost valid JSON object
                for start in range(len(candidate)):
                    if candidate[start] == "{":
                        depth = 0
                        for end in range(start, len(candidate)):
                            if candidate[end] == "{":
                                depth += 1
                            elif candidate[end] == "}":
                                depth -= 1
                            if depth == 0:
                                try:
                                    return json.loads(candidate[start : end + 1])
                                except json.JSONDecodeError:
                                    break
                                break

        return None
    except Exception as exc:
        logger.warning("parse_json_from_llm failed: %s", exc)
        return None


def clamp_score(score: Any, low: float = 0.0, high: float = 10.0) -> float:
    """
    Clamp numeric score to valid range.

    Args:
        score: Value to clamp (converted to float).
        low: Minimum allowed score.
        high: Maximum allowed score.

    Returns:
        Clamped float value, or 0.0 if conversion fails.
    """
    try:
        val = float(score)
        return max(low, min(high, val))
    except (TypeError, ValueError):
        return 0.0


def list_to_bullets(items: List[str]) -> str:
    """
    Format list of strings as bullet-point text for storage/display.

    Args:
        items: List of text items.

    Returns:
        Newline-separated bullet string, or empty string if no items.
    """
    try:
        if not items:
            return ""
        return "\n".join(f"• {item}" for item in items if item)
    except Exception as exc:
        logger.warning("list_to_bullets failed: %s", exc)
        return ""


def bullets_to_list(text: str) -> List[str]:
    """
    Parse bullet-point string back to a list.

    Args:
        text: Bullet-formatted string.

    Returns:
        List of stripped text items.
    """
    try:
        if not text:
            return []
        lines = text.split("\n")
        result: List[str] = []
        for line in lines:
            line = line.strip()
            if line.startswith("•"):
                result.append(line[1:].strip())
            elif line.startswith("-"):
                result.append(line[1:].strip())
            elif line:
                result.append(line)
        return result
    except Exception as exc:
        logger.warning("bullets_to_list failed: %s", exc)
        return []


def truncate_text(text: str, max_len: int = 500) -> str:
    """
    Truncate long text with ellipsis.

    Args:
        text: Text to truncate.
        max_len: Maximum character length.

    Returns:
        Truncated text with ``...`` suffix if needed.
    """
    try:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."
    except Exception as exc:
        logger.warning("truncate_text failed: %s", exc)
        return text or ""


def difficulty_order(difficulty: str) -> int:
    """
    Return numeric order for difficulty comparison.

    Args:
        difficulty: Difficulty string (easy/medium/hard).

    Returns:
        Integer ordering: easy=0, medium=1, hard=2.
    """
    mapping = {"easy": 0, "medium": 1, "hard": 2}
    return mapping.get(difficulty.lower(), 1)


def adjust_difficulty(current: str, score: float, increase_at: float, decrease_at: float) -> str:
    """
    Adjust difficulty based on answer score.

    Increases difficulty when ``score > increase_at`` and decreases when
    ``score < decrease_at``.

    Args:
        current: Current difficulty level.
        score: Score from the latest answer.
        increase_at: Threshold to increase difficulty.
        decrease_at: Threshold to decrease difficulty.

    Returns:
        New difficulty level string.
    """
    try:
        levels = ["easy", "medium", "hard"]
        idx = difficulty_order(current)
        if score > increase_at and idx < 2:
            return levels[idx + 1]
        if score < decrease_at and idx > 0:
            return levels[idx - 1]
        return current.lower()
    except Exception as exc:
        logger.warning("adjust_difficulty failed: %s", exc)
        return current.lower()


def resume_context_summary(
    skills: List[str],
    projects: List[Dict[str, str]],
    education: List[Dict[str, str]],
    experience_snippet: str = "",
) -> str:
    """
    Build compact resume context string for inclusion in LLM prompts.

    Args:
        skills: List of skill names.
        projects: List of project dicts with title/description/technologies.
        education: List of education dicts with degree/institution/year.
        experience_snippet: Short text excerpt from resume.

    Returns:
        Formatted multi-line context string.
    """
    try:
        parts: List[str] = []
        if skills:
            parts.append(f"Skills: {', '.join(skills[:30])}")
        if projects:
            proj_lines = [
                f"- {p.get('title', '')}: {p.get('description', '')[:120]}"
                for p in projects[:5]
            ]
            parts.append("Projects:\n" + "\n".join(proj_lines))
        if education:
            edu_lines = [
                f"- {e.get('degree', '')} at {e.get('institution', '')} ({e.get('year', '')})"
                for e in education[:5]
            ]
            parts.append("Education:\n" + "\n".join(edu_lines))
        if experience_snippet:
            parts.append(f"Experience excerpt:\n{experience_snippet[:800]}")
        return "\n\n".join(parts) if parts else "No resume data available."
    except Exception as exc:
        logger.warning("resume_context_summary failed: %s", exc)
        return "No resume data available."
