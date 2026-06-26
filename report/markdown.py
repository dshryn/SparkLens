from .models import Report


class MarkdownRenderer:
    """
    Renders a Report as Markdown.
    """

    def render(
        self,
        report: Report,
    ) -> str:

        lines = [
            f"# {report.title}",
            "",
            "## Executive Summary",
            "",
            report.summary,
            "",
        ]

        if report.findings:
            lines.extend([
                "## Findings",
                "",
            ])

            for finding in report.findings:

                lines.append(f"### {finding.title}")
                lines.append(f"Severity: **{finding.severity}**")

                if finding.operator_name:
                    lines.append(
                        f"Operator: **{finding.operator_name}**"
                    )

                lines.extend([
                    "",
                    finding.description,
                    "",
                ])

        if report.recommendations:
            lines.extend([
                "## Recommendations",
                "",
            ])

            for recommendation in report.recommendations:
                lines.append(f"- {recommendation}")

            lines.append("")

        if report.insights:
            lines.extend([
                "## AI Insights",
                "",
            ])

            for insight in report.insights:
                lines.extend([
                    f"### {insight.title}",
                    f"Category: **{insight.category}**",
                    "",
                    insight.description,
                    "",
                ])

        for section in report.sections:
            lines.extend([
                f"## {section.title}",
                "",
                section.content,
                "",
            ])

        return "\n".join(lines)

    def save(
        self,
        report: Report,
        path: str,
    ) -> None:

        content = self.render(report)

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(content)