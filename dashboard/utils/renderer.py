from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from report.exporters import (
    pipeline_to_json,
    report_to_html,
    report_to_markdown,
)
from services.pipeline import PipelineResult
from dashboard.components.ui import ai_panel, finding_card, metric_card


def render_metrics(result: PipelineResult) -> None:
    """
    Render top-level execution metrics.
    """

    stats = result.analysis.statistics

    metrics = (
        ("Operators", stats.operator_count, "◈"),
        ("Joins", stats.join_count, "⟷"),
        ("Shuffles", stats.shuffle_count, "⇄"),
        ("Stages", stats.stage_count, "▦"),
        ("Findings", len(result.analysis.report.findings), "!"),
        ("Complexity", stats.complexity, "◒"),
    )
    columns = st.columns(len(metrics))
    for column, (label, value, icon) in zip(columns, metrics):
        with column:
            metric_card(label, value, icon)


def render_health(result: PipelineResult) -> None:
    stats = result.analysis.statistics
    findings = result.analysis.report.findings
    critical = sum(
        finding.severity.value in {"Critical", "High"}
        for finding in findings
    )
    if stats.operator_count:
        score = max(0, round(100 - (critical * 12) - (stats.shuffle_count * 3)))
    else:
        score = 0
    tone = "#22c55e" if score >= 80 else "#f59e0b" if score >= 55 else "#ef4444"
    label = "Healthy" if score >= 80 else "Needs attention" if score >= 55 else "Review findings"
    st.markdown(
        f'<div class="sl-card sl-card-accent">'
        f'<div class="sl-eyebrow">Execution health · heuristic</div>'
        f'<div style="display:flex;align-items:end;gap:.65rem">'
        f'<span style="font-size:2.2rem;font-weight:750;color:{tone}">{score}</span>'
        f'<span class="sl-muted" style="padding-bottom:.35rem">/ 100 · {label}</span></div>'
        f'<div style="height:7px;background:#26334d;border-radius:8px;margin-top:.75rem">'
        f'<div style="height:7px;width:{score}%;background:{tone};border-radius:8px"></div></div>'
        f'<div class="sl-muted" style="font-size:.75rem;margin-top:.55rem">'
        f"Derived from deterministic findings and shuffle count; not runtime telemetry.</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_overview(result: PipelineResult) -> None:
    """
    Render execution summary.
    """

    stats = result.analysis.statistics

    st.subheader("Pipeline Summary")

    st.markdown(f"""
- **Operators:** {stats.operator_count}
- **Stages:** {stats.stage_count}
- **Joins:** {stats.join_count}
- **Shuffle Exchanges:** {stats.shuffle_count}
- **Execution Complexity:** **{stats.complexity}**
""")

    with st.expander(
        "Execution Statistics",
        expanded=True,
    ):

        st.write(
            {
                "Edges": stats.edge_count,
                "Root Nodes": stats.root_node_count,
                "Leaf Nodes": stats.leaf_node_count,
                "Max Depth": stats.max_depth,
                "Broadcast Joins": stats.broadcast_join_count,
                "Exchanges": stats.exchange_count,
                "Aggregations": stats.aggregate_count,
                "Sorts": stats.sort_count,
                "Filters": stats.filter_count,
                "Scans": stats.scan_count,
                "Complexity Score": stats.complexity_score,
            }
        )


def render_findings(
    result: PipelineResult,
) -> None:
    """
    Render deterministic findings.
    """

    st.subheader("Detected Findings")

    findings = result.analysis.report.findings
    if not findings:
        st.success("No optimization issues detected.")
        return

    filters = ["All", "Critical", "High", "Medium", "Low"]
    selected = st.radio(
        "Severity",
        filters,
        index=0,
        key="finding_severity_filter",
        horizontal=True,
    )
    query = st.text_input(
        "Search findings",
        placeholder="Search by title, rule, operator, or description",
        key="finding_search",
    ).lower()
    visible = [
        finding
        for finding in findings
        if (selected == "All" or finding.severity.value == selected)
        and (
            not query
            or query in finding.title.lower()
            or query in finding.rule.lower()
            or query in finding.description.lower()
        )
    ]
    if not visible:
        st.info("No findings match the current filter.")
        return
    for index, finding in enumerate(visible):
        operator = (
            result.analysis.dag.get_operator(finding.operator_id).name
            if finding.operator_id is not None
            else None
        )
        if finding_card(finding, operator, f"finding_{index}"):
            if finding.operator_id is not None:
                st.session_state["selected_operator_id"] = finding.operator_id
                st.info(f"Selected operator {finding.operator_id}: {operator}")


def render_dag(
    result: PipelineResult,
) -> None:
    """
    Render the interactive execution DAG.
    """

    from visualization.dag import DAGVisualizer

    st.subheader("Execution DAG")

    visualizer = DAGVisualizer()

    html = visualizer.to_html(
        result.analysis.dag,
        result.analysis.report,
    )

    components.html(
        html,
        height=850,
        scrolling=True,
    )


def render_ai(
    result: PipelineResult,
) -> None:
    """
    Render AI explanation.
    """

    explanation = result.explanation

    ai_panel(explanation)


def render_downloads(
    result: PipelineResult,
) -> None:
    """
    Render report download buttons.
    """

    html_report = report_to_html(result.report)
    markdown_report = report_to_markdown(result.report)
    json_report = pipeline_to_json(result)

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        label="Download HTML Report",
        data=html_report,
        file_name="sparklens_report.html",
        mime="text/html",
        use_container_width=True,
    )

    c2.download_button(
        label="Download Markdown Report",
        data=markdown_report,
        file_name="sparklens_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

    c3.download_button(
        label="Download JSON",
        data=json_report,
        file_name="sparklens_analysis.json",
        mime="application/json",
        use_container_width=True,
    )
