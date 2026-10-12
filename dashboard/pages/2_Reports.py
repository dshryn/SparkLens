import streamlit as st

from dashboard.components.ui import empty_state, page_header
from dashboard.styles.theme import apply_theme, render_sidebar
from dashboard.utils.renderer import render_downloads

apply_theme()
render_sidebar()
page_header(
    "Report center",
    "Reports",
    "Export and review the latest deterministic and AI-assisted analysis.",
)

result = st.session_state.get("analysis_result")
if result is None:
    empty_state(
        "No saved reports yet",
        "Analyze an execution plan first. The latest result will be available here.",
    )
else:
    stats = result.analysis.statistics
    st.markdown("### Latest analysis")
    st.markdown(
        f'<div class="sl-card">Latest result: <b>{stats.operator_count}</b> operators · '
        f'<b>{len(result.analysis.report.findings)}</b> findings · '
        f'complexity <b>{stats.complexity}</b></div>',
        unsafe_allow_html=True,
    )
    render_downloads(result)
