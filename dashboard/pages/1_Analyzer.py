import streamlit as st

from dashboard.services.analysis_service import (
    analyze_execution_plan,
)

from dashboard.utils.renderer import (
    render_ai,
    render_dag,
    render_downloads,
    render_findings,
    render_metrics,
    render_overview,
)

st.set_page_config(
    page_title="SparkLens Analyzer",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ SparkLens Analyzer")
st.caption("Explainable Spark Execution Plan Analyzer")


with st.sidebar:

    st.header("Execution Plan")

    uploaded_file = st.file_uploader(
        "Upload Plan",
        type=["txt"],
    )

    st.divider()

    st.subheader("Or Paste Plan")

    plan_text = st.text_area(
        "",
        height=250,
        placeholder="Paste Spark physical execution plan...",
    )

    st.divider()

    enable_ai = st.checkbox(
        "Enable AI",
        value=True,
    )

    analyze = st.button(
        "🚀 Analyze",
        use_container_width=True,
    )


result = None

if analyze:

    if uploaded_file is not None:

        plan = uploaded_file.read().decode("utf-8")

    else:

        plan = plan_text.strip()

    if not plan:

        st.error("Please upload or paste an execution plan.")

    else:

        with st.spinner("Analyzing execution plan..."):

            result = analyze_execution_plan(
                plan_text=plan,
                enable_ai=enable_ai,
            )

        st.success("Analysis Complete")

else:

    st.info("Upload or paste an execution plan and click Analyze.")


if result is not None:

    st.divider()

    render_metrics(result)

    st.divider()

    (
        overview_tab,
        findings_tab,
        dag_tab,
        ai_tab,
    ) = st.tabs(
        [
            "Overview",
            "Findings",
            "Execution DAG",
            "AI Analysis",
        ]
    )

    with overview_tab:
        render_overview(result)

    with findings_tab:
        render_findings(result)

    with dag_tab:
        render_dag(result)

    with ai_tab:
        render_ai(result)

    st.divider()

    render_downloads(result)
