from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    """Apply the shared SparkLens visual language to the current page."""

    st.markdown(
        """
        <style>
        :root {
          --sl-bg: #0b1020;
          --sl-surface: #111827;
          --sl-surface-raised: #172033;
          --sl-border: #26334d;
          --sl-text: #e5edf8;
          --sl-muted: #91a0b8;
          --sl-accent: #8b5cf6;
          --sl-cyan: #38bdf8;
          --sl-green: #22c55e;
          --sl-amber: #f59e0b;
          --sl-orange: #f97316;
          --sl-red: #ef4444;
        }
        .stApp {
          background: var(--sl-bg);
          color: var(--sl-text);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
          background: #0d1425;
          border-right: 1px solid var(--sl-border);
        }
        h1, h2, h3 { letter-spacing: -0.02em; }
        h1 { font-weight: 700; }
        .sl-eyebrow {
          color: var(--sl-cyan);
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.13em;
          text-transform: uppercase;
          margin-bottom: 0.4rem;
        }
        .sl-subtitle, .sl-muted { color: var(--sl-muted); }
        .sl-sidebar-brand {
          align-items: center;
          color: var(--sl-text);
          display: flex;
          gap: .65rem;
          margin: .25rem 0 1.5rem;
        }
        .sl-sidebar-mark { color: #fbbf24; font-size: 1.25rem; }
        .sl-sidebar-brand small {
          color: var(--sl-muted);
          display: block;
          font-size: .62rem;
          font-weight: 400;
          margin-top: .15rem;
        }
        .sl-sidebar-section {
          color: #61718c;
          font-size: .65rem;
          font-weight: 750;
          letter-spacing: .12em;
          margin: 1.1rem 0 .35rem;
          text-transform: uppercase;
        }
        .sl-hero { margin: 2.5rem auto 2rem; max-width: 760px; text-align: center; }
        .sl-hero-mark { color: #fbbf24; font-size: 2.35rem; margin-bottom: .8rem; }
        .sl-hero h1 { font-size: 3rem; margin: .15rem 0 .35rem; }
        .sl-hero-tagline { color: var(--sl-text); font-size: 1.15rem; font-weight: 600; }
        .sl-hero p { color: var(--sl-muted); margin: .55rem 0 0; }
        .sl-start-card {
          background: var(--sl-surface);
          border: 1px solid var(--sl-border);
          border-left: 3px solid var(--sl-accent);
          border-radius: 10px;
          min-height: 142px;
          padding: 1rem 1.15rem;
        }
        .sl-start-card-quiet { border-left-color: var(--sl-cyan); }
        .sl-start-card h3 { margin: .25rem 0 .35rem; }
        .sl-start-card p { font-size: .88rem; margin: 0; }
        .st-key-landing-cta-left .stButton,
        .st-key-landing-cta-right .stButton { margin-top: 10px; }
        .sl-section-heading { margin: 2.65rem 0 .85rem; }
        .sl-section-heading h2 { font-size: 1.35rem; margin: 0; }
        .sl-step {
          border-top: 1px solid var(--sl-border);
          min-height: 95px;
          padding: .8rem .25rem;
        }
        .sl-step span {
          color: var(--sl-accent);
          display: block;
          font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: .72rem;
          font-weight: 750;
          margin-bottom: .45rem;
        }
        .sl-step b, .sl-step small, .sl-capability b, .sl-capability small {
          display: block;
        }
        .sl-step small, .sl-capability small { color: var(--sl-muted); font-size: .78rem; margin-top: .3rem; }
        .sl-capability-heading { margin-top: 1.6rem; }
        .sl-capability {
          background: rgba(17, 24, 39, .72);
          border: 1px solid var(--sl-border);
          border-radius: 9px;
          min-height: 108px;
          padding: .85rem .95rem;
        }
        .sl-capability > span { color: var(--sl-cyan); display: block; font-size: 1.05rem; margin-bottom: .55rem; }
        .sl-footer-note {
          color: #697a95;
          font-size: .75rem;
          margin: 2.4rem 0 1rem;
          text-align: center;
        }
        .sl-card {
          background: var(--sl-surface);
          border: 1px solid var(--sl-border);
          border-radius: 10px;
          padding: 1rem 1.1rem;
          margin: 0.35rem 0;
        }
        .sl-card-accent { border-top: 2px solid var(--sl-accent); }
        .sl-metric-value {
          color: var(--sl-text);
          font-size: 1.65rem;
          font-weight: 750;
          line-height: 1.1;
        }
        .sl-metric-label {
          color: var(--sl-muted);
          font-size: 0.78rem;
          margin-top: 0.35rem;
        }
        .sl-metric-icon { color: var(--sl-accent); float: right; font-size: 1.1rem; }
        .sl-finding {
          background: var(--sl-surface);
          border: 1px solid var(--sl-border);
          border-left: 4px solid var(--sl-accent);
          border-radius: 8px;
          padding: 0.85rem 1rem;
          margin: 0.5rem 0;
        }
        .sl-finding-title { color: var(--sl-text); font-weight: 650; }
        .sl-finding-meta { color: var(--sl-muted); font-size: 0.8rem; margin-top: 0.25rem; }
        .sl-finding-description { color: #c6d2e5; font-size: 0.9rem; margin-top: 0.55rem; }
        .sl-pill {
          border-radius: 999px;
          display: inline-block;
          font-size: 0.68rem;
          font-weight: 750;
          letter-spacing: 0.05em;
          padding: 0.18rem 0.5rem;
          text-transform: uppercase;
        }
        .sl-empty {
          background: var(--sl-surface);
          border: 1px dashed #40506d;
          border-radius: 12px;
          padding: 2.8rem 1rem;
          text-align: center;
        }
        .sl-empty-icon { color: var(--sl-accent); font-size: 2rem; }
        .sl-ai {
          background: linear-gradient(135deg, #15152e 0%, #111827 65%);
          border: 1px solid #493d78;
          border-radius: 12px;
          padding: 1.15rem 1.25rem;
        }
        .sl-ai-title { color: #c4b5fd; font-size: 1.05rem; font-weight: 700; }
        .stButton > button, .stDownloadButton > button {
          border-radius: 7px;
          border: 1px solid var(--sl-border);
          font-weight: 650;
        }
        .stButton > button[kind="primary"] {
          background: var(--sl-accent);
          border-color: var(--sl-accent);
          color: white;
        }
        textarea, code, pre {
          font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important;
        }
        textarea {
          background: #0a1120 !important;
          border-color: var(--sl-border) !important;
          color: #dbeafe !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render the shared SparkLens navigation shell on every page."""

    with st.sidebar:
        st.markdown(
            '<div class="sl-sidebar-brand">'
            '<span class="sl-sidebar-mark">⚡</span>'
            '<span><b>SparkLens</b><small>Spark Execution Intelligence</small></span>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sl-sidebar-section">Analyze</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/1_Analyzer.py", label="Analyzer", icon="⚡")
        st.markdown(
            '<div class="sl-sidebar-section">Explore</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/2_Reports.py", label="Reports", icon="📄")
        st.page_link("pages/3_DAG.py", label="DAG", icon="🕸️")
        st.markdown(
            '<div class="sl-sidebar-section">System</div>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/4_Settings.py", label="Settings", icon="⚙️")


def severity_style(severity: str) -> tuple[str, str]:
    styles = {
        "Critical": ("#ef4444", "#fee2e2"),
        "High": ("#f97316", "#ffedd5"),
        "Medium": ("#f59e0b", "#fef3c7"),
        "Low": ("#22c55e", "#dcfce7"),
    }
    return styles.get(severity, ("#8b5cf6", "#ede9fe"))
