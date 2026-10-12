from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="SparkLens",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("home.py", title="SparkLens", url_path="", default=True),
    st.Page("pages/1_Analyzer.py", title="Analyzer", url_path="Analyzer"),
    st.Page("pages/2_Reports.py", title="Reports", url_path="Reports"),
    st.Page("pages/3_DAG.py", title="DAG", url_path="DAG"),
    st.Page("pages/4_Settings.py", title="Settings", url_path="Settings"),
]

st.navigation(pages, position="hidden").run()
