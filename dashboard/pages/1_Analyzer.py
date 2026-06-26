import streamlit as st

st.set_page_config(
    page_title="SparkLens Analyzer",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ SparkLens Analyzer")
st.caption("Explainable Spark Execution Plan Analyzer")

with st.sidebar:

    st.header("Execution Plan")

    uploaded_file = st.file_uploader(
        "Upload Plan",
        type=["txt"]
    )

    st.divider()

    st.subheader("Or Paste Plan")

    plan_text = st.text_area(
        "",
        height=250,
        placeholder="Paste Spark physical execution plan..."
    )

    st.divider()

    analyze = st.button(
        "🚀 Analyze",
        use_container_width=True
    )

    st.divider()

    st.subheader("Options")

    enable_ai = st.checkbox(
        "Enable AI",
        value=True
    )

if analyze:
    st.success("Analysis Complete")
else:
    st.info("Upload or paste an execution plan and click Analyze.")

st.divider()

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Operators", "32")
c2.metric("Joins", "4")
c3.metric("Shuffles", "3")
c4.metric("Stages", "8")
c5.metric("Findings", "12")
c6.metric("Complexity", "High")

st.divider()

overview_tab, findings_tab, dag_tab, ai_tab = st.tabs(
    [
        "Overview",
        "Findings",
        "Execution DAG",
        "AI Analysis"
    ]
)

with overview_tab:

    st.subheader("Pipeline Summary")

    st.markdown("""
- Broadcast Hash Join detected
- Multiple shuffle exchanges detected
- AQE enabled
- High execution complexity
""")

    with st.expander(
        "Optimization Recommendations",
        expanded=True
    ):

        st.markdown("- Enable Broadcast Join where possible")
        st.markdown("- Reduce unnecessary shuffle exchanges")
        st.markdown("- Tune spark.sql.shuffle.partitions")

with findings_tab:

    st.subheader("Detected Findings")

    st.dataframe(
        [
            {
                "Severity": "High",
                "Rule": "Shuffle Rule",
                "Operator": "Exchange",
                "Description": "Multiple shuffle exchanges detected."
            },
            {
                "Severity": "Medium",
                "Rule": "Join Rule",
                "Operator": "BroadcastHashJoin",
                "Description": "Broadcast opportunity found."
            }
        ],
        use_container_width=True,
        hide_index=True
    )

with dag_tab:

    st.subheader("Execution DAG")

    st.info("Interactive DAG visualization will be rendered here.")

with ai_tab:

    st.subheader("AI Explanation")

    st.markdown("""
The execution plan contains several shuffle-heavy operations.

The Broadcast Hash Join is a good choice for one side of the join, but the number of exchanges indicates unnecessary data movement.

Enabling AQE and reducing shuffle partitions could improve execution performance.
""")

st.divider()

download_col1, download_col2, download_col3 = st.columns(3)

download_col1.download_button(
    "Download HTML Report",
    data="Coming Soon",
    file_name="report.html"
)

download_col2.download_button(
    "Download Markdown Report",
    data="Coming Soon",
    file_name="report.md"
)

download_col3.download_button(
    "Download JSON",
    data="Coming Soon",
    file_name="analysis.json"
)