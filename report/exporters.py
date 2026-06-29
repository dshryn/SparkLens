from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from report.models import Report

if TYPE_CHECKING:
    from services.pipeline import PipelineResult


def report_to_markdown(
    report: Report,
) -> str:
    """
    Converts a Report into Markdown.
    """

    lines: list[str] = []

    lines.append(f"# {report.title}")
    lines.append("")
    lines.append(report.summary)
    lines.append("")

    if report.sections:
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

    if report.findings:
        lines.append("## Findings")
        lines.append("")

        for finding in report.findings:
            lines.append(f"### {finding.title}")
            lines.append(f"- Severity: **{finding.severity}**")

            if finding.operator_name:
                lines.append(f"- Operator: **{finding.operator_name}**")

            lines.append("")
            lines.append(finding.description)
            lines.append("")

    if report.recommendations:
        lines.append("## Recommendations")
        lines.append("")

        for recommendation in report.recommendations:
            lines.append(f"- {recommendation}")

        lines.append("")

    if report.insights:
        lines.append("## Insights")
        lines.append("")

        for insight in report.insights:
            lines.append(f"### {insight.title}")
            lines.append(f"**Category:** {insight.category}")
            lines.append("")
            lines.append(insight.description)
            lines.append("")

    return "\n".join(lines)


def report_to_html(
    report: Report,
) -> str:
    """
    Converts a Report into HTML.
    """

    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        f"<title>{report.title}</title>",
        """
        <style>
        body{
            font-family:Arial,Helvetica,sans-serif;
            max-width:1000px;
            margin:auto;
            padding:40px;
            line-height:1.6;
        }
        h1,h2,h3{
            color:#222;
        }
        table{
            border-collapse:collapse;
            width:100%;
        }
        th,td{
            border:1px solid #ddd;
            padding:8px;
        }
        th{
            background:#f5f5f5;
        }
        </style>
        """,
        "</head>",
        "<body>",
        f"<h1>{report.title}</h1>",
        f"<p>{report.summary}</p>",
    ]

    for section in report.sections:
        html.append(f"<h2>{section.title}</h2>")
        html.append("<p>" + section.content.replace("\n", "<br>") + "</p>")

    if report.findings:

        html.append("<h2>Findings</h2>")
        html.append(
            "<table>"
            "<tr>"
            "<th>Title</th>"
            "<th>Severity</th>"
            "<th>Operator</th>"
            "<th>Description</th>"
            "</tr>"
        )

        for finding in report.findings:
            html.append(
                "<tr>"
                f"<td>{finding.title}</td>"
                f"<td>{finding.severity}</td>"
                f"<td>{finding.operator_name or '-'}</td>"
                f"<td>{finding.description}</td>"
                "</tr>"
            )

        html.append("</table>")

    if report.recommendations:

        html.append("<h2>Recommendations</h2>")
        html.append("<ul>")

        for recommendation in report.recommendations:
            html.append(f"<li>{recommendation}</li>")

        html.append("</ul>")

    if report.insights:

        html.append("<h2>Insights</h2>")

        for insight in report.insights:
            html.append(f"<h3>{insight.title}</h3>")
            html.append(f"<b>Category:</b> {insight.category}")
            html.append(f"<p>{insight.description}</p>")

    html.extend(
        [
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(html)


def pipeline_to_json(
    result: PipelineResult,
) -> str:
    """
    Serializes the complete PipelineResult as JSON.
    """

    return json.dumps(
        asdict(result),
        indent=2,
        default=str,
    )
