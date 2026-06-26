from .models import Report


class HTMLRenderer:
    """
    Renders a Report as HTML.
    """

    def render(
        self,
        report: Report,
    ) -> str:

        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset=\"utf-8\">",
            f"<title>{report.title}</title>",
            "</head>",
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
                ])

                if finding.operator_name:
                    html.append(
                        f"<p><strong>Operator:</strong> {finding.operator_name}</p>"
                    )

                html.append(
                    f"<p>{finding.description}</p>"
                )

        if report.recommendations:
            html.extend([
                "<h2>Recommendations</h2>",
                "<ul>",
            ])

            for recommendation in report.recommendations:
                html.append(
                    f"<li>{recommendation}</li>"
                )

            html.append("</ul>")

        if report.insights:
            html.append("<h2>AI Insights</h2>")

            for insight in report.insights:
                html.extend([
                    f"<h3>{insight.title}</h3>",
                    f"<p><strong>Category:</strong> {insight.category}</p>",
                    f"<p>{insight.description}</p>",
                ])

        for section in report.sections:
            html.extend([
                f"<h2>{section.title}</h2>",
                f"<p>{section.content.replace(chr(10), '<br>')}</p>",
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