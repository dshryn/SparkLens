from __future__ import annotations

import streamlit as st

from dashboard.styles.theme import severity_style


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="sl-eyebrow">{eyebrow}</div>'
        f"<h1>{title}</h1>"
        f'<div class="sl-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: object, icon: str = "") -> None:
    st.markdown(
        f'<div class="sl-card">'
        f'<span class="sl-metric-icon">{icon}</span>'
        f'<div class="sl-metric-value">{value}</div>'
        f'<div class="sl-metric-label">{label}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def empty_state(title: str, message: str) -> None:
    st.markdown(
        f'<div class="sl-empty">'
        f'<div class="sl-empty-icon">⚡</div>'
        f"<h3>{title}</h3>"
        f'<div class="sl-muted">{message}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def finding_card(finding, operator_name: str | None, key: str) -> bool:
    """Render a finding and return whether its details action was selected."""

    severity = finding.severity.value
    color, background = severity_style(severity)
    operator = operator_name or "Plan-level observation"
    st.markdown(
        f'<div class="sl-finding" style="border-left-color:{color}">'
        f'<span class="sl-pill" style="color:{color};background:{background}">'
        f"{severity}</span> "
        f'<span class="sl-finding-title">{finding.title}</span>'
        f'<div class="sl-finding-meta">{finding.rule} · Operator: {operator}</div>'
        f'<div class="sl-finding-description">{finding.description}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    return st.button("View operator details", key=key, use_container_width=False)


def ai_panel(explanation) -> None:
    st.markdown(
        '<div class="sl-ai"><div class="sl-ai-title">✦ SparkLens AI</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{explanation.summary}**")
    st.markdown(explanation.explanation)

    if explanation.recommendations:
        st.markdown("#### Recommendations")
        for recommendation in explanation.recommendations:
            st.markdown(f"- {recommendation}")

    if explanation.insights:
        st.markdown("#### Additional insights")
        for insight in explanation.insights:
            st.markdown(f"**{insight.title}**  \n{insight.description}")

    st.markdown("</div>", unsafe_allow_html=True)
