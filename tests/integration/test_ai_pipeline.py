import os

from dotenv import load_dotenv

from ai.explainer import Explainer
from ai.models import AIConfig
from ai.providers.gemini_provider import GeminiProvider

from analyzer.analyzer import SparkAnalyzer

from report import (
    ReportGenerator,
    MarkdownRenderer,
    HTMLRenderer,
)

from tests.utils import load_sample_plan

load_dotenv()


def test_ai_pipeline():
    api_key = os.getenv("GEMINI_API_KEY")

    assert api_key is not None, (
        "GEMINI_API_KEY environment variable is not set."
    )

    analyzer = SparkAnalyzer()

    analysis = analyzer.analyze_plan(
        load_sample_plan("broadcast_join")
    )

    provider = GeminiProvider(
        AIConfig(api_key=api_key)
    )

    explainer = Explainer(provider)

    explanation = explainer.explain(analysis)

    assert explanation.summary
    assert explanation.explanation
    assert explanation.recommendations

    report = ReportGenerator().generate(
        analysis,
        explanation,
    )

    markdown = MarkdownRenderer().render(
        report
    )

    html = HTMLRenderer().render(
        report
    )

    assert markdown
    assert html

    assert "SparkLens Analysis Report" in markdown
    assert "<html>" in html