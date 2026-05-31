"""Analytics data transfer objects (non-ORM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TopicPerformance:
    """Performance metrics for a single topic."""

    topic: str
    avg_score: float
    question_count: int


@dataclass
class SessionSummary:
    """Summary row for interview history table."""

    session_id: int
    interview_type: str
    difficulty: str
    avg_score: float
    total_score: float
    status: str
    started_at: datetime
    completed_at: Optional[datetime]


@dataclass
class AnalyticsDashboard:
    """Aggregated analytics for dashboard display."""

    total_interviews: int = 0
    average_score: float = 0.0
    scores_by_type: Dict[str, float] = field(default_factory=dict)
    improvement_trend: List[Dict[str, Any]] = field(default_factory=list)
    topic_performance: List[TopicPerformance] = field(default_factory=list)
    recent_sessions: List[SessionSummary] = field(default_factory=list)
