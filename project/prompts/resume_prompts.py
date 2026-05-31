"""Prompt templates for resume parsing and analysis."""

from __future__ import annotations


def resume_extraction_prompt(resume_text: str) -> str:
    """
    Build prompt to extract structured resume data.

    Args:
        resume_text: Raw text extracted from PDF.

    Returns:
        Formatted prompt string.
    """
    return f"""You are an expert resume parser. Extract structured information from the resume below.

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "skills": [
    {{"skill_name": "Python", "category": "programming"}},
    {{"skill_name": "SQL", "category": "database"}}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "description": "Brief description",
      "technologies": "Python, Flask"
    }}
  ],
  "education": [
    {{
      "degree": "B.Tech Computer Science",
      "institution": "University Name",
      "year": "2022"
    }}
  ],
  "experience_summary": "2-3 sentence summary of work experience from the resume"
}}

Rules:
- Extract all relevant skills with appropriate categories (programming, framework, database, cloud, soft, etc.)
- Include personal and academic projects if present
- Include all education entries
- If a section is missing, use empty arrays and empty string for experience_summary
- Be accurate; do not invent credentials not in the resume

RESUME TEXT:
{resume_text[:12000]}
"""
