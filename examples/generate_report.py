from ai.models import AIExplanation

from analyzer.analyzer import SparkAnalyzer

from report import (
    ReportGenerator,
    MarkdownRenderer,
    HTMLRenderer,
)

from tests.utils import load_sample_plan


def main():
    analyzer = SparkAnalyzer()

    analysis = analyzer.analyze_plan(
        load_sample_plan("broadcast_join")
    )

    explanation = AIExplanation(
        summary="Sample SparkLens summary",
        explanation="Sample SparkLens explanation",
        recommendations=[
            "Reduce unnecessary shuffles.",
            "Consider broadcast joins.",
        ],
        model="local",
    )

    report = ReportGenerator().generate(
        analysis,
        explanation,
    )

    MarkdownRenderer().save(
        report,
        "report.md",
    )

    HTMLRenderer().save(
        report,
        "report.html",
    )

    print("Generated report.md")
    print("Generated report.html")


if __name__ == "__main__":
    main()