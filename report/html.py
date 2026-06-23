from .models import Report


class HTMLRenderer:
    def render(self, report: Report) -> str:
        html = [
            "<html>",
            "<body>",
            f"<h1>{report.title}</h1>",
            "<h2>Executive Summary</h2>",
            f"<p>{report.summary}</p>",
        ]

        if report.findings:
            html.append("<h2>Findings</h2>")

            for finding in report.findings:
                html.extend([
                    f"<h3>{finding.title}</h3>",
                    f"<p><strong>Severity:</strong> {finding.severity}</p>",
                    f"<p>{finding.description}</p>",
                ])

        if report.recommendations:
            html.append("<h2>Recommendations</h2>")
            html.append("<ul>")

            for recommendation in report.recommendations:
                html.append(f"<li>{recommendation}</li>")

            html.append("</ul>")

        for section in report.sections:
            html.extend([
                f"<h2>{section.title}</h2>",
                f"<p>{section.content}</p>",
            ])

        html.extend([
            "</body>",
            "</html>",
        ])

        return "\n".join(html)

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