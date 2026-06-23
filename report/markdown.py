from .models import Report


class MarkdownRenderer:
    def render(self, report: Report) -> str:
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
                lines.extend([
                    f"### {finding.title}",
                    f"Severity: **{finding.severity}**",
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