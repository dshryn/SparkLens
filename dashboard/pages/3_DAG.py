from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from visualization.dag import DAGVisualizer
from visualization.interactive_renderer import (
    InteractiveRenderer,
)
from dashboard.components.ui import empty_state, page_header
from dashboard.styles.theme import apply_theme, render_sidebar

apply_theme()
render_sidebar()

page_header(
    "Graph explorer",
    "DAG Explorer",
    "Inspect the operator graph and the severity signals attached to it.",
)

result = st.session_state.get("analysis_result")

if result is None:

    empty_state(
        "No graph available",
        "Analyze a Spark execution plan from the Analyzer page first.",
    )

    st.stop()

st.success("Displaying interactive execution graph.")

visualizer = DAGVisualizer(
    renderer=InteractiveRenderer(),
)

output_path = Path("execution_dag.html")

visualizer.save(
    result.analysis.dag,
    result.analysis.report,
    str(output_path),
)

components.html(
    output_path.read_text(
        encoding="utf-8",
    ),
    height=850,
    scrolling=True,
)

st.divider()

stats = result.analysis.statistics

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Operators",
    stats.operator_count,
)

c2.metric(
    "Edges",
    stats.edge_count,
)

c3.metric(
    "Stages",
    stats.stage_count,
)

c4.metric(
    "Complexity",
    stats.complexity,
)

st.divider()

with st.expander(
    "Graph Legend",
    expanded=False,
):

    st.markdown("""
### Node Colors

- 🟢 Low Severity
- 🟡 Medium Severity
- 🟠 High Severity
- 🔴 Critical Severity
- 🔵 No Findings

### Navigation

- Drag nodes to rearrange the graph.
- Scroll to zoom.
- Click and drag the background to pan.
- Hover over nodes to inspect operator details.
""")
