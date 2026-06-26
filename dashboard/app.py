import streamlit as st

st.set_page_config(
    page_title="SparkLens",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("SparkLens")

st.subheader("Explainable Spark Execution Plan Analyzer")

st.markdown("""
SparkLens is an offline analysis framework for Apache Spark execution plans.

### Features

- Deterministic rule-based analysis
- Interactive execution plan visualization
- AI-generated explanations
- HTML & Markdown reports
- Optimization recommendations

---

👈 Use the sidebar to begin analyzing a Spark execution plan.
""")

st.info("Current Version: v0.3")