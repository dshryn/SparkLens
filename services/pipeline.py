from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from analyzer.analyzer import SparkAnalyzer

from ai.explainer import Explainer
from ai.models import AIConfig
from ai.models import AIExplanation
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.retrying_provider import RetryingProvider

from models.analysis_result import AnalysisResult

from report.generator import ReportGenerator
from report.models import Report


load_dotenv()


@dataclass(slots=True)
class PipelineResult:
    analysis: AnalysisResult
    explanation: AIExplanation
    report: Report


class AnalysisPipeline:
    """
    High-level SparkLens orchestration.

    Responsible for:
    - Deterministic analysis
    - AI explanation (optional)
    - Report generation

    NOT responsible for:
    - CLI
    - Streamlit
    - Saving files
    """

    def __init__(self) -> None:
        self._analyzer = SparkAnalyzer()

    def run(
        self,
        plan: str,
        enable_ai: bool = True,
    ) -> PipelineResult:

        analysis = self._analyzer.analyze_plan(
            plan
        )

        if enable_ai:

            api_key = os.getenv(
                "GEMINI_API_KEY"
            )

            if api_key:

                provider = RetryingProvider(
                    GeminiProvider(
                        AIConfig(
                            api_key=api_key,
                        )
                    ),
                    max_attempts=3,
                    initial_delay=1.0,
                )

                explainer = Explainer(
                    provider
                )

                explanation = explainer.explain(
                    analysis
                )

            else:

                explanation = AIExplanation(
                    summary="Gemini API key not configured.",
                    explanation=(
                        "Deterministic analysis completed successfully, "
                        "but AI explanation could not be generated."
                    ),
                    recommendations=[],
                    insights=[],
                    model="none",
                )

        else:

            explanation = AIExplanation(
                summary="AI explanation disabled.",
                explanation=(
                    "Only deterministic analysis was executed."
                ),
                recommendations=[],
                insights=[],
                model="none",
            )

        report = ReportGenerator().generate(
            analysis,
            explanation,
        )

        return PipelineResult(
            analysis=analysis,
            explanation=explanation,
            report=report,
        )