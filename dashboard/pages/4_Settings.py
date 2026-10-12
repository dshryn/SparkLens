import streamlit as st

from dashboard.components.ui import page_header
from dashboard.styles.theme import apply_theme, render_sidebar

apply_theme()
render_sidebar()
page_header(
    "Workspace preferences",
    "Settings",
    "Keep the analyzer focused without hiding important controls.",
)

st.markdown("### Analysis")
st.session_state["enable_ai"] = st.toggle(
    "Enable AI by default",
    value=st.session_state.get("enable_ai", True),
    help="The Analyzer page still lets you override this for an individual run.",
)
st.session_state["auto_analyze_default"] = st.toggle(
    "Auto Analyze by default",
    value=st.session_state.get("auto_analyze_default", False),
    help="Live preview always disables AI and only runs deterministic analysis.",
)

st.markdown("### Appearance")
st.info("SparkLens currently uses the dark observability theme.")

st.markdown("### About")
st.markdown(
    '<div class="sl-card"><b>SparkLens</b><br>'
    '<span class="sl-muted">Version 0.3 · Explainable Spark Execution Plan Analyzer</span>'
    "</div>",
    unsafe_allow_html=True,
)
