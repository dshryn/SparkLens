from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

from analyzer.analyzer import SparkAnalyzer

from ai.explainer import Explainer
from ai.models import AIConfig
from ai.models import AIExplanation
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.retrying_provider import RetryingProvider

from report.generator import ReportGenerator
from report.html import HTMLRenderer
from report.markdown import MarkdownRenderer

from visualization.dag import DAGVisualizer


load_dotenv()


@dataclass
class PipelineResult:

    analysis: object

    explanation: AIExplanation

    report: object

    dag_path: str

    markdown_path: str

    html_path: str


class AnalysisPipeline:

    def __init__(self):

        self._analyzer = SparkAnalyzer()

    def run(
        self,
        plan: str,
        enable_ai: bool = True,
    ) -> PipelineResult:

        analysis = self._analyzer.analyze_plan(
            plan
        )

        DAGVisualizer().save(
            analysis.dag,
            analysis.report,
            "dag.png",
        )

        if enable_ai:

            api_key = os.getenv(
                "GEMINI_API_KEY"
            )

            if not api_key:

                explanation = AIExplanation(
                    summary="No API key configured.",
                    explanation="Gemini API key not found.",
                    recommendations=[],
                    model="none",
                )

            else:

                provider = RetryingProvider(
                    GeminiProvider(
                        AIConfig(
                            api_key=api_key
                        )
                    ),
                    max_attempts=3,
                    initial_delay=1.0,
                )

                explanation = Explainer(
                    provider
                ).explain(
                    analysis
                )

        else:

            explanation = AIExplanation(
                summary="AI disabled.",
                explanation="Only deterministic analysis executed.",
                recommendations=[],
                model="none",
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

        return PipelineResult(
            analysis=analysis,
            explanation=explanation,
            report=report,
            dag_path="dag.png",
            markdown_path="report.md",
            html_path="report.html",
        )