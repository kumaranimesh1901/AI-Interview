"""Analytics dashboard page with Plotly charts."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.analytics_engine import analytics_engine
from config.settings import configure_logging
from utils.streamlit_auth import get_db_session, render_sidebar, require_login

configure_logging()
logger = logging.getLogger(__name__)

require_login()
render_sidebar()

st.title("📊 Analytics Dashboard")

db = get_db_session()
try:
    dashboard = analytics_engine.load_dashboard(db, st.session_state.user_id)

    if dashboard.total_interviews == 0:
        st.info("No completed interviews yet. Complete an interview to see analytics.")
        st.page_link("pages/4_interview.py", label="Start Interview", icon="🎤")
        st.stop()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Interviews", dashboard.total_interviews)
    m2.metric("Average Score", f"{dashboard.average_score:.2f} / 10")
    m3.metric(
        "Interview Types Practiced",
        len(dashboard.scores_by_type),
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_bar = analytics_engine.scores_by_type_chart(dashboard.scores_by_type)
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        fig_line = analytics_engine.improvement_trend_chart(dashboard.improvement_trend)
        st.plotly_chart(fig_line, use_container_width=True)

    fig_radar = analytics_engine.topic_radar_chart(dashboard.topic_performance)
    st.plotly_chart(fig_radar, use_container_width=True)

    st.subheader("Recent Interview History")
    rows = analytics_engine.sessions_to_dataframe_rows(dashboard.recent_sessions)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No interview history yet.")

except Exception as exc:
    logger.exception("Analytics page error: %s", exc)
    st.error(f"Failed to load analytics: {exc}")
finally:
    db.close()
