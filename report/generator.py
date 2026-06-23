from .models import (
    Report,
    ReportFinding,
    ReportSection,
)

from models.analysis_result import AnalysisResult
from ai.models import AIExplanation


class ReportGenerator:
    def generate(
        self,
        analysis: AnalysisResult,
        explanation: AIExplanation,
    ) -> Report:

        findings = [
            ReportFinding(
                title=finding.title,
                description=finding.description,
                severity=finding.severity.value,
            )
            for finding in analysis.report.findings
        ]

        overview = ReportSection(
            title="Execution Overview",
            content=(
                f"Operators: {len(analysis.dag.operators)}\n"
                f"Findings: {len(analysis.report.findings)}\n"
                f"Root Nodes: {len(analysis.dag.root_nodes())}\n"
                f"Leaf Nodes: {len(analysis.dag.leaf_nodes())}"
            ),
        )

        ai_explanation = ReportSection(
            title="AI Explanation",
            content=explanation.explanation,
        )

        return Report(
            title="SparkLens Analysis Report",
            summary=explanation.summary,
            findings=findings,
            recommendations=explanation.recommendations,
            sections=[
                overview,
                ai_explanation,
            ],
        )