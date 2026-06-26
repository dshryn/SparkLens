import logging
import os

import pytest
from dotenv import load_dotenv

from ai.exceptions import AITransientError
from ai.explainer import Explainer
from ai.models import AIConfig
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.retrying_provider import RetryingProvider

from analyzer.analyzer import SparkAnalyzer

from report import (
    ReportGenerator,
    MarkdownRenderer,
    HTMLRenderer,
)

from tests.utils import load_sample_plan

load_dotenv()

logger = logging.getLogger(__name__)


def test_ai_pipeline():

    api_key = os.getenv("GEMINI_API_KEY")

    assert api_key is not None, (
        "GEMINI_API_KEY environment variable is not set."
    )

    logger.info("=" * 80)
    logger.info("SparkLens AI Pipeline Integration Test Started")
    logger.info("=" * 80)

    analyzer = SparkAnalyzer()

    logger.info("[Stage 1] Loading sample execution plan...")

    plan = load_sample_plan(
        "broadcast_join"
    )

    logger.info(
        "[Stage 2] Running deterministic analyzer..."
    )

    analysis = analyzer.analyze_plan(plan)

    logger.info(
        "Analysis complete"
    )
    logger.info(
        "Operators: %d",
        len(analysis.dag.operators),
    )
    logger.info(
        "Edges: %d",
        len(analysis.dag.edges),
    )
    logger.info(
        "Findings: %d",
        len(analysis.report.findings),
    )

    provider = RetryingProvider(
        GeminiProvider(
            AIConfig(api_key=api_key)
        )
    )

    explainer = Explainer(provider)

    logger.info(
        "[Stage 3] Requesting AI explanation..."
    )

    try:

        explanation = explainer.explain(
            analysis
        )

    except AITransientError:

        logger.warning(
            "Gemini temporarily unavailable."
        )

        pytest.skip(
            "Gemini temporarily unavailable."
        )

    logger.info(
        "AI explanation generated successfully."
    )

    logger.info(
        "Summary Length: %d",
        len(explanation.summary),
    )

    logger.info(
        "Recommendations: %d",
        len(explanation.recommendations),
    )

    logger.info(
        "Insights: %d",
        len(explanation.insights),
    )

    logger.info(
        "[Stage 4] Generating report..."
    )

    report = ReportGenerator().generate(
        analysis,
        explanation,
    )

    logger.info(
        "Report generated."
    )

    logger.info(
        "Report Findings: %d",
        len(report.findings),
    )

    logger.info(
        "Report Recommendations: %d",
        len(report.recommendations),
    )

    logger.info(
        "Report Insights: %d",
        len(report.insights),
    )

    logger.info(
        "[Stage 5] Rendering Markdown..."
    )

    markdown = MarkdownRenderer().render(
        report
    )

    logger.info(
        "Markdown rendered successfully."
    )

    logger.info(
        "[Stage 6] Rendering HTML..."
    )

    html = HTMLRenderer().render(
        report
    )

    logger.info(
        "HTML rendered successfully."
    )

    logger.info(
        "[Stage 7] Validating outputs..."
    )

    assert explanation.summary
    assert explanation.explanation
    assert explanation.recommendations

    assert report.summary
    assert report.findings
    assert report.recommendations

    assert markdown
    assert html

    assert "SparkLens Analysis Report" in markdown
    assert "<html>" in html

    if explanation.insights:
        assert report.insights
        assert "AI Insights" in markdown
        assert "AI Insights" in html

    logger.info("=" * 80)
    logger.info("SparkLens AI Pipeline Integration Test Passed")
    logger.info("=" * 80)