from __future__ import annotations

import hashlib

import streamlit as st

from dashboard.components.ui import empty_state, page_header
from dashboard.styles.theme import apply_theme, render_sidebar
from dashboard.ui_services.analysis_service import analyze_execution_plan
from dashboard.utils.renderer import (
    render_ai,
    render_dag,
    render_downloads,
    render_findings,
    render_health,
    render_metrics,
    render_overview,
)


SAMPLE_PLAN = """== Physical Plan ==
(1) FileScan
Output [1]: [id, value]
Arguments: parquet scan

(2) Filter
Input [1]: [id, value]
Condition: value > 10

(3) BroadcastHashJoin
Left keys [1]: [id]
Right keys [1]: [id]
Join type: Inner
"""


def _run_analysis(plan: str, enable_ai: bool) -> None:
    with st.spinner("Analyzing execution plan..."):
        st.session_state["analysis_result"] = analyze_execution_plan(
            plan_text=plan,
            enable_ai=enable_ai,
        )
    st.session_state["last_analyzed_plan"] = plan


def _load_sample() -> None:
    st.session_state["plan_editor"] = SAMPLE_PLAN


def _clear_editor() -> None:
    st.session_state["plan_editor"] = ""
    st.session_state.pop("analysis_result", None)


apply_theme()
render_sidebar()

if "plan_editor" not in st.session_state:
    st.session_state["plan_editor"] = ""

page_header(
    "SparkLens workbench",
    "Analyze a Spark execution plan",
    "Understand operators, shuffles, findings, and recommendations in one workspace.",
)

left, right = st.columns([1.05, 1], gap="large")
with left:
    st.markdown('<div class="sl-eyebrow">Execution plan</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload a formatted Spark plan",
        type=["txt"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        st.session_state["plan_editor"] = uploaded_file.getvalue().decode(
            "utf-8",
            errors="replace",
        )

    plan_text = st.text_area(
        "Plan editor",
        height=430,
        placeholder="Paste a Spark physical execution plan here...",
        key="plan_editor",
        label_visibility="collapsed",
    )
    st.caption("Formatted explain plans are supported. The editor is intentionally monospace for large plans.")

with right:
    st.markdown('<div class="sl-eyebrow">Live execution DAG</div>', unsafe_allow_html=True)
    current_result = st.session_state.get("analysis_result")
    if current_result is None:
        empty_state(
            "No execution plan loaded",
            "Paste a physical plan or upload a .txt file to preview its execution graph.",
        )
    else:
        render_dag(current_result)

st.divider()
control_1, control_2, control_3, control_4, control_5 = st.columns(
    [1.2, 1.2, 1.2, 1.5, 1.5],
    vertical_alignment="center",
)
with control_1:
    st.button(
        "Use sample plan",
        on_click=_load_sample,
        use_container_width=True,
    )
with control_2:
    st.button(
        "Clear editor",
        on_click=_clear_editor,
        use_container_width=True,
    )
with control_3:
    auto_analyze = st.toggle(
        "Auto Analyze",
        value=st.session_state.get("auto_analyze_default", False),
    )
with control_4:
    enable_ai = st.toggle(
        "Enable AI",
        value=st.session_state.get("enable_ai", True),
        help="AI is only executed by the full Analyze action, never by live preview.",
    )
    st.session_state["enable_ai"] = enable_ai
with control_5:
    analyze = st.button("⚡ Analyze", type="primary", use_container_width=True)

plan = plan_text.strip()
plan_hash = hashlib.sha256(plan.encode("utf-8")).hexdigest()
if auto_analyze and plan and plan_hash != st.session_state.get("live_plan_hash"):
    # Live preview deliberately disables AI. The explicit Analyze action below
    # remains the only path that can invoke the optional provider.
    with st.spinner("Updating deterministic preview..."):
        st.session_state["analysis_result"] = analyze_execution_plan(
            plan_text=plan,
            enable_ai=False,
        )
    st.session_state["live_plan_hash"] = plan_hash

if analyze:
    if not plan:
        st.error("Add a plan before analyzing.")
    else:
        _run_analysis(plan, enable_ai)
        st.session_state["live_plan_hash"] = plan_hash
        result = st.session_state["analysis_result"]
        stats = result.analysis.statistics
        st.success(
            f"Analysis complete · {stats.operator_count} operators · "
            f"{stats.join_count} joins · {len(result.analysis.report.findings)} findings"
        )

result = st.session_state.get("analysis_result")
if result is None:
    st.divider()
    empty_state(
        "Ready when you are",
        "Paste a plan, use the sample, or upload a .txt file to begin.",
    )
else:
    st.divider()
    st.markdown('<div class="sl-eyebrow">Execution health</div>', unsafe_allow_html=True)
    health, summary = st.columns([1, 2], gap="large")
    with health:
        render_health(result)
    with summary:
        render_metrics(result)

    st.divider()
    findings_col, ai_col = st.columns([1.15, 0.85], gap="large")
    with findings_col:
        st.markdown("### Findings")
        render_findings(result)
    with ai_col:
        st.markdown("### SparkLens AI")
        render_ai(result)

    with st.expander("Execution overview", expanded=False):
        render_overview(result)

    st.divider()
    render_downloads(result)
