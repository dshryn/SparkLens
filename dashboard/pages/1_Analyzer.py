import streamlit as st
from services.analysis_service import analyze_execution_plan

st.title("Execution Plan Analyzer")

uploaded_file = st.file_uploader(
    "Upload Spark Execution Plan",
    type=["txt"]
)

st.divider()

plan_text = st.text_area(
    "Or paste the execution plan",
    height=250,
    placeholder="Paste Spark physical execution plan here..."
)

analyze = st.button(
    "Analyze",
    use_container_width=True
)

st.divider()

st.header("Execution Summary")

summary_placeholder = st.empty()

st.divider()

st.header("Execution DAG")

dag_placeholder = st.empty()

st.divider()

st.header("Findings")

findings_placeholder = st.empty()

st.divider()

st.header("Recommendations")

recommendation_placeholder = st.empty()

st.divider()

st.header("AI Explanation")

ai_placeholder = st.empty()

if analyze:

    with st.spinner("Analyzing execution plan..."):

        result = analyze_execution_plan(plan_text)

    st.success("Analysis Complete")

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Operators", result.summary["operators"])
    c2.metric("Joins", result.summary["joins"])
    c3.metric("Shuffles", result.summary["shuffles"])
    c4.metric("Complexity", result.summary["complexity"])

    st.divider()

    st.subheader("Findings")

    st.table(result.findings)

    st.divider()

    st.subheader("Recommendations")

    for recommendation in result.recommendations:
        st.markdown(f"- {recommendation}")

    st.divider()

    st.subheader("AI Summary")

    st.markdown(result.ai_summary)