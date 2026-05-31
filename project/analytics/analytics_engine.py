"""Analytics aggregation and Plotly chart builders."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from sqlalchemy.orm import Session

from database import crud
from models.analytics import AnalyticsDashboard, SessionSummary, TopicPerformance

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Computes dashboard metrics and visualization figures."""

    def load_dashboard(self, db: Session, user_id: int) -> AnalyticsDashboard:
        """
        Build complete analytics dashboard data.

        Args:
            db: Database session.
            user_id: Current user ID.

        Returns:
            AnalyticsDashboard dataclass instance.
        """
        try:
            agg = crud.get_analytics_aggregates(db, user_id)
            sessions = agg.get("sessions", [])

            improvement_trend: List[Dict[str, Any]] = []
            sorted_sessions = sorted(
                [s for s in sessions if s.completed_at],
                key=lambda s: s.completed_at or s.started_at,
            )
            for idx, s in enumerate(sorted_sessions, start=1):
                improvement_trend.append(
                    {
                        "session_index": idx,
                        "date": (s.completed_at or s.started_at).strftime("%Y-%m-%d"),
                        "avg_score": round(s.avg_score, 2),
                        "interview_type": s.interview_type,
                    }
                )

            topic_performance: List[TopicPerformance] = []
            for row in agg.get("topic_rows", []):
                topic_performance.append(
                    TopicPerformance(
                        topic=row.topic or "general",
                        avg_score=round(float(row.avg_score or 0), 2),
                        question_count=int(row.cnt or 0),
                    )
                )

            recent: List[SessionSummary] = []
            for s in crud.get_user_sessions(db, user_id, limit=20):
                recent.append(
                    SessionSummary(
                        session_id=s.id,
                        interview_type=s.interview_type,
                        difficulty=s.difficulty,
                        avg_score=round(s.avg_score, 2),
                        total_score=round(s.total_score, 2),
                        status=s.status,
                        started_at=s.started_at,
                        completed_at=s.completed_at,
                    )
                )

            return AnalyticsDashboard(
                total_interviews=agg.get("total_interviews", 0),
                average_score=agg.get("average_score", 0.0),
                scores_by_type=agg.get("scores_by_type", {}),
                improvement_trend=improvement_trend,
                topic_performance=topic_performance,
                recent_sessions=recent,
            )
        except Exception as exc:
            logger.exception("load_dashboard failed: %s", exc)
            return AnalyticsDashboard()

    def scores_by_type_chart(self, scores_by_type: Dict[str, float]) -> Figure:
        """Bar chart of average score per interview type."""
        try:
            if not scores_by_type:
                fig = go.Figure()
                fig.update_layout(
                    title="Average Score by Interview Type",
                    annotations=[
                        dict(
                            text="No completed interviews yet",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                        )
                    ],
                )
                return fig

            types = list(scores_by_type.keys())
            scores = list(scores_by_type.values())
            fig = px.bar(
                x=types,
                y=scores,
                labels={"x": "Interview Type", "y": "Average Score"},
                title="Average Score by Interview Type",
                color=types,
            )
            fig.update_layout(showlegend=False, yaxis_range=[0, 10])
            return fig
        except Exception as exc:
            logger.exception("scores_by_type_chart failed: %s", exc)
            return go.Figure()

    def improvement_trend_chart(self, trend: List[Dict[str, Any]]) -> Figure:
        """Line chart of score improvement over sessions."""
        try:
            if not trend:
                fig = go.Figure()
                fig.update_layout(
                    title="Score Improvement Over Time",
                    annotations=[
                        dict(
                            text="Complete interviews to see trends",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                        )
                    ],
                )
                return fig

            fig = px.line(
                trend,
                x="session_index",
                y="avg_score",
                markers=True,
                hover_data=["date", "interview_type"],
                labels={
                    "session_index": "Session #",
                    "avg_score": "Average Score",
                },
                title="Score Improvement Over Time",
            )
            fig.update_layout(yaxis_range=[0, 10])
            return fig
        except Exception as exc:
            logger.exception("improvement_trend_chart failed: %s", exc)
            return go.Figure()

    def topic_radar_chart(
        self,
        topic_performance: List[TopicPerformance],
    ) -> Figure:
        """Radar chart of topic-wise performance."""
        try:
            if not topic_performance:
                fig = go.Figure()
                fig.update_layout(
                    title="Topic-wise Performance",
                    annotations=[
                        dict(
                            text="No topic data available",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                        )
                    ],
                )
                return fig

            topics = [t.topic for t in topic_performance]
            scores = [t.avg_score for t in topic_performance]

            fig = go.Figure()
            fig.add_trace(
                go.Scatterpolar(
                    r=scores + [scores[0]],
                    theta=topics + [topics[0]],
                    fill="toself",
                    name="Avg Score",
                )
            )
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                title="Topic-wise Performance",
                showlegend=False,
            )
            return fig
        except Exception as exc:
            logger.exception("topic_radar_chart failed: %s", exc)
            return go.Figure()

    def sessions_to_dataframe_rows(
        self,
        sessions: List[SessionSummary],
    ) -> List[Dict[str, Any]]:
        """Convert session summaries to table rows."""
        try:
            rows: List[Dict[str, Any]] = []
            for s in sessions:
                rows.append(
                    {
                        "ID": s.session_id,
                        "Type": s.interview_type,
                        "Difficulty": s.difficulty,
                        "Avg Score": s.avg_score,
                        "Total Score": s.total_score,
                        "Status": s.status,
                        "Started": s.started_at.strftime("%Y-%m-%d %H:%M")
                        if isinstance(s.started_at, datetime)
                        else str(s.started_at),
                        "Completed": (
                            s.completed_at.strftime("%Y-%m-%d %H:%M")
                            if s.completed_at
                            else "-"
                        ),
                    }
                )
            return rows
        except Exception as exc:
            logger.exception("sessions_to_dataframe_rows failed: %s", exc)
            return []


analytics_engine = AnalyticsEngine()
