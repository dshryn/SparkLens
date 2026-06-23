from pathlib import Path

from ai.models import AIExplanation

from analyzer.analyzer import SparkAnalyzer

from report import (
    ReportGenerator,
    MarkdownRenderer,
    HTMLRenderer,
)

from tests.utils import load_sample_plan


def test_end_to_end():
    analyzer = SparkAnalyzer()

    analysis = analyzer.analyze_plan(
        load_sample_plan("broadcast_join")
    )

    explanation = AIExplanation(
        summary="Test summary",
        explanation="Test explanation",
        recommendations=[
            "Test recommendation"
        ],
        model="test-model",
    )

    report = ReportGenerator().generate(
        analysis,
        explanation,
    )

    markdown_path = "report.md"
    html_path = "report.html"

    MarkdownRenderer().save(
        report,
        markdown_path,
    )

    HTMLRenderer().save(
        report,
        html_path,
    )

    
    assert Path(markdown_path).exists()
    assert Path(html_path).exists()