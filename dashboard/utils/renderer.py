from __future__ import annotations

import streamlit as st

from services.pipeline import PipelineResult


def render_metrics(result: PipelineResult) -> None:
    """
    Render top-level execution metrics.
    """

    stats = result.analysis.statistics

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Operators", stats.operator_count)
    c2.metric("Joins", stats.join_count)
    c3.metric("Shuffles", stats.shuffle_count)
    c4.metric("Stages", stats.stage_count)
    c5.metric(
        "Findings",
        len(result.analysis.report.findings),
    )
    c6.metric(
        "Complexity",
        stats.complexity,
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

    rows = []

    for finding in result.analysis.report.findings:

        operator = None

        if finding.operator_id is not None:
            operator = result.analysis.dag.get_operator(finding.operator_id).name

        rows.append(
            {
                "Severity": finding.severity.value,
                "Rule": finding.rule,
                "Operator": operator,
                "Description": finding.description,
            }
        )

    if rows:
        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No optimization issues detected.")


def render_dag(
    result: PipelineResult,
) -> None:
    """
    Placeholder for future DAG visualization.
    """

    st.subheader("Execution DAG")

    st.info("Interactive DAG visualization coming soon.")


def render_ai(
    result: PipelineResult,
) -> None:
    """
    Render AI explanation.
    """

    explanation = result.explanation

    st.subheader("AI Explanation")

    st.markdown(explanation.explanation)

    if explanation.recommendations:

        st.divider()

        st.subheader("Recommendations")

        for recommendation in explanation.recommendations:
            st.markdown(f"- {recommendation}")

    if explanation.insights:

        st.divider()

        st.subheader("Insights")

        for insight in explanation.insights:
            st.markdown(f"**{insight.title}**\n\n" f"{insight.description}")


def render_downloads(
    result: PipelineResult,
) -> None:
    """
    Placeholder download buttons.
    """

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download HTML Report",
        data="Coming Soon",
        file_name="report.html",
    )

    c2.download_button(
        "Download Markdown Report",
        data="Coming Soon",
        file_name="report.md",
    )

    c3.download_button(
        "Download JSON",
        data="Coming Soon",
        file_name="analysis.json",
    )
