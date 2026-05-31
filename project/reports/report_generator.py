"""PDF report generation using ReportLab."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config.settings import settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates interview session PDF reports using ReportLab."""

    def __init__(self) -> None:
        """Ensure reports directory exists on construction."""
        try:
            settings.ensure_directories()
        except Exception as exc:
            logger.exception("ReportGenerator init failed: %s", exc)
            raise

    def generate(self, data: Dict[str, Any], session_id: int) -> Path:
        """
        Create a full PDF interview report.

        Args:
            data: Report payload containing user info, session metadata,
                  and a ``qa_pairs`` list of question/answer dicts.
            session_id: Interview session ID (used in the filename).

        Returns:
            Path to the generated PDF file.

        Raises:
            Exception: If PDF generation fails.
        """
        try:
            filename = f"interview_report_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = settings.REPORTS_DIR / filename

            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=18,
                spaceAfter=12,
            )
            heading_style = styles["Heading2"]
            body_style = styles["BodyText"]
            small_style = ParagraphStyle(
                "Small",
                parent=body_style,
                fontSize=9,
                leading=12,
            )

            story: List[Any] = []

            # --- Title ---
            story.append(Paragraph("AI Interview Preparation Report", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # --- User & session info ---
            info_lines = [
                f"<b>Candidate:</b> {self._escape(data.get('username', 'N/A'))}",
                f"<b>Email:</b> {self._escape(data.get('email', 'N/A'))}",
                f"<b>Interview Type:</b> {self._escape(data.get('interview_type', 'N/A'))}",
                f"<b>Difficulty:</b> {self._escape(data.get('difficulty', 'N/A'))}",
                f"<b>Status:</b> {self._escape(data.get('status', 'N/A'))}",
                f"<b>Total Score:</b> {data.get('total_score', 0):.1f}",
                f"<b>Average Score:</b> {data.get('avg_score', 0):.2f} / 10",
            ]
            started = data.get("started_at")
            completed = data.get("completed_at")
            if started:
                ts = started.strftime('%Y-%m-%d %H:%M UTC') if hasattr(started, 'strftime') else str(started)
                info_lines.append(f"<b>Started:</b> {ts}")
            if completed:
                ts = completed.strftime('%Y-%m-%d %H:%M UTC') if hasattr(completed, 'strftime') else str(completed)
                info_lines.append(f"<b>Completed:</b> {ts}")

            for line in info_lines:
                story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 0.3 * inch))

            # --- Summary table ---
            qa_pairs: List[Dict[str, Any]] = data.get("qa_pairs", [])
            if qa_pairs:
                summary_data = [["Q#", "Topic", "Difficulty", "Score"]]
                for qa in qa_pairs:
                    summary_data.append(
                        [
                            str(qa.get("question_number", "")),
                            str(qa.get("topic", ""))[:30],
                            str(qa.get("difficulty", "")),
                            f"{qa.get('score', 0):.1f}",
                        ]
                    )
                summary_table = Table(summary_data, colWidths=[40, 180, 70, 60])
                summary_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#E8EEF7")]),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("ALIGN", (1, 1), (1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                story.append(Paragraph("Performance Summary", heading_style))
                story.append(Spacer(1, 0.1 * inch))
                story.append(summary_table)
                story.append(Spacer(1, 0.3 * inch))

            # --- Detailed Q&A ---
            story.append(Paragraph("Detailed Questions, Answers &amp; Feedback", heading_style))
            story.append(Spacer(1, 0.15 * inch))

            for qa in qa_pairs:
                qnum = qa.get("question_number", "?")
                diff = self._escape(str(qa.get("difficulty", "")))
                topic = self._escape(str(qa.get("topic", "")))

                story.append(
                    Paragraph(
                        f"Question {qnum} ({diff} | {topic})",
                        heading_style,
                    )
                )

                q_text = self._escape(str(qa.get("question", "")))
                a_text = self._escape(str(qa.get("answer", "")))
                story.append(Paragraph(f"<b>Q:</b> {q_text}", body_style))
                story.append(Paragraph(f"<b>A:</b> {a_text}", body_style))
                story.append(
                    Paragraph(f"<b>Score:</b> {qa.get('score', 0):.1f} / 10", body_style)
                )

                strengths = self._escape(str(qa.get("strengths", "")))
                weaknesses = self._escape(str(qa.get("weaknesses", "")))
                missing = self._escape(str(qa.get("missing_concepts", "")))
                improved = self._escape(str(qa.get("improved_answer", "")))

                # Convert newlines to <br/> AFTER escaping to avoid double-escape
                story.append(
                    Paragraph(
                        f"<b>Strengths:</b><br/>{strengths.replace(chr(10), '<br/>')}",
                        small_style,
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Weaknesses:</b><br/>{weaknesses.replace(chr(10), '<br/>')}",
                        small_style,
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Missing Concepts:</b><br/>{missing.replace(chr(10), '<br/>')}",
                        small_style,
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Improved Answer:</b> {improved}",
                        small_style,
                    )
                )
                story.append(Spacer(1, 0.2 * inch))

            # --- Overall summary ---
            avg = float(data.get("avg_score", 0))
            if avg >= 8:
                verdict = "Excellent performance. Strong readiness for interviews."
            elif avg >= 6:
                verdict = "Good performance with room for improvement in weak areas."
            elif avg >= 4:
                verdict = "Moderate performance. Focus on missing concepts highlighted above."
            else:
                verdict = "Needs significant improvement. Review model answers and practice more."

            story.append(Paragraph("Overall Performance Summary", heading_style))
            story.append(Paragraph(verdict, body_style))
            story.append(
                Paragraph(
                    f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                    small_style,
                )
            )

            doc.build(story)
            logger.info("Report saved to %s", output_path)
            return output_path
        except Exception as exc:
            logger.exception("generate failed: %s", exc)
            raise

    @staticmethod
    def _escape(text: str) -> str:
        """
        Escape XML special characters for ReportLab Paragraph markup.

        Must be applied BEFORE inserting any ReportLab XML tags (``<b>``,
        ``<br/>``, etc.) to avoid double-escaping.

        Args:
            text: Raw text that may contain &, <, > characters.

        Returns:
            XML-safe string.
        """
        try:
            if not text:
                return ""
            return (
                str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
        except Exception:
            return ""
