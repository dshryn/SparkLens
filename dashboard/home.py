from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from dashboard.styles.theme import apply_theme, render_sidebar

SAMPLE_PLAN = """== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[region#12], functions=[sum(amount#3)])
   +- Exchange hashpartitioning(region#12, 200), ENSURE_REQUIREMENTS, [plan_id=45]
      +- HashAggregate(keys=[region#12], functions=[partial_sum(amount#3)])
         +- Project [amount#3, region#12]
            +- BroadcastHashJoin [customer_id#2], [customer_id#10], Inner, BuildRight, false
               :- Filter (isnotnull(amount#3) AND (amount#3 > 100))
               :  +- FileScan parquet [customer_id#2,amount#3] Batched: true,
               DataFilters: [isnotnull(amount#3), (amount#3 > 100)], Format: Parquet, Location:
               InMemoryFileIndex(1 paths)[file:/warehouse/orders], PartitionFilters: [], PushedFilters:
               [IsNotNull(amount), GreaterThan(amount,100)], ReadSchema:
               struct<customer_id:int,amount:int>
               +- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int,
               false] as bigint)),false), [plan_id=40]
                  +- FileScan parquet [customer_id#10,region#12] Batched: true,
                  DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)
                  [file:/warehouse/customers], PartitionFilters: [], PushedFilters: [], ReadSchema:
                  struct<customer_id:int,region:string>
"""


def open_analyzer() -> None:
    st.switch_page("pages/1_Analyzer.py")


def open_sample() -> None:
    st.session_state["plan_editor"] = SAMPLE_PLAN
    st.switch_page("pages/1_Analyzer.py")


apply_theme()
render_sidebar()

st.markdown(
    '<section class="sl-hero">'
    '<div class="sl-hero-mark">⚡</div>'
    '<div class="sl-eyebrow">Spark execution intelligence</div>'
    '<h1>SparkLens</h1>'
    '<div class="sl-hero-tagline">Understand. Diagnose. Optimize.</div>'
    '<p>Your Spark physical plan, explained.</p>'
    "</section>",
    unsafe_allow_html=True,
)

cta_left, cta_right = st.columns([1, 1], gap="small")
with cta_left:
    with st.container(key="landing-cta-left"):
        st.markdown(
            '<div class="sl-start-card">'
            '<div class="sl-eyebrow">Start here</div>'
            "<h3>Analyze a Spark execution plan</h3>"
            '<p class="sl-muted">Upload or paste a formatted physical plan to see its '
            "DAG, findings, and recommendations.</p></div>",
            unsafe_allow_html=True,
        )
        st.button(
            "⚡  Analyze a Spark Plan",
            type="primary",
            use_container_width=True,
            on_click=open_analyzer,
        )
with cta_right:
    with st.container(key="landing-cta-right"):
        st.markdown(
            '<div class="sl-start-card sl-start-card-quiet">'
            '<div class="sl-eyebrow">Quick start</div>'
            "<h3>See it in action</h3>"
            '<p class="sl-muted">Load a small sample plan and explore the complete '
            "analysis workflow.</p></div>",
            unsafe_allow_html=True,
        )
        st.button(
            "Try Sample Plan",
            use_container_width=True,
            on_click=open_sample,
        )

st.markdown(
    '<div class="sl-section-heading">'
    '<div class="sl-eyebrow">The workflow</div>'
    "<h2>How SparkLens works</h2></div>",
    unsafe_allow_html=True,
)

steps = st.columns(4, gap="small")
for column, number, title, description in zip(
    steps,
    ("01", "02", "03", "04"),
    ("Parse", "Diagnose", "Explain", "Optimize"),
    (
        "Understand the execution plan",
        "Detect expensive operations",
        "See why they matter",
        "Get actionable recommendations",
    ),
):
    with column:
        st.markdown(
            f'<div class="sl-step"><span>{number}</span><b>{title}</b>'
            f"<small>{description}</small></div>",
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="sl-section-heading sl-capability-heading">'
    '<div class="sl-eyebrow">Built for Spark engineers</div>'
    "<h2>Everything you need to read the plan</h2></div>",
    unsafe_allow_html=True,
)

capabilities = st.columns(4, gap="small")
for column, icon, title, description in zip(
    capabilities,
    ("⚡", "◈", "✦", "↓"),
    ("Execution DAG", "Optimization", "AI insights", "Reports"),
    (
        "Visualize your Spark execution graph.",
        "Detect costly Spark patterns.",
        "Understand why the plan matters.",
        "Export analysis results.",
    ),
):
    with column:
        st.markdown(
            f'<div class="sl-capability"><span>{icon}</span><b>{title}</b>'
            f"<small>{description}</small></div>",
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="sl-footer-note">Deterministic analysis first. '
    "AI explains, never replaces the analysis.</div>",
    unsafe_allow_html=True,
)
