from ai.models import AIExplanation

from models.analysis_result import AnalysisResult

from .models import (
    Report,
    ReportFinding,
    ReportInsight,
    ReportSection,
)


class ReportGenerator:
    """
    Generates a structured report from deterministic SparkLens analysis
    and AI-generated explanations.
    """

    def generate(
        self,
        analysis: AnalysisResult,
        explanation: AIExplanation,
    ) -> Report:

        return Report(
            title="SparkLens Analysis Report",
            summary=explanation.summary,
            findings=self._build_findings(analysis),
            recommendations=explanation.recommendations,
            insights=self._build_insights(explanation),
            sections=[
                self._build_overview(analysis),
                self._build_ai_explanation(explanation),
            ],
        )

    def _build_findings(
        self,
        analysis: AnalysisResult,
    ) -> list[ReportFinding]:
        """
        Converts deterministic analysis findings into report findings.
        """

        findings: list[ReportFinding] = []

        for finding in analysis.report.findings:

            operator_name = None

            if finding.operator_id is not None:
                operator = analysis.dag.get_operator(
                    finding.operator_id
                )
                operator_name = operator.name

            findings.append(
                ReportFinding(
                    title=finding.title,
                    description=finding.description,
                    severity=finding.severity.value,
                    operator_name=operator_name,
                )
            )

        return findings

    def _build_overview(
        self,
        analysis: AnalysisResult,
    ) -> ReportSection:
        """
        Builds the execution overview section.
        """

        return ReportSection(
            title="Execution Overview",
            content=(
                f"Operators: {len(analysis.dag.operators)}\n"
                f"Edges: {len(analysis.dag.edges)}\n"
                f"Findings: {len(analysis.report.findings)}\n"
                f"Root Nodes: {len(analysis.dag.root_nodes())}\n"
                f"Leaf Nodes: {len(analysis.dag.leaf_nodes())}"
            ),
        )

    def _build_ai_explanation(
        self,
        explanation: AIExplanation,
    ) -> ReportSection:
        """
        Builds the AI explanation section.
        """

        return ReportSection(
            title="AI Explanation",
            content=explanation.explanation,
        )

    def _build_insights(
        self,
        explanation: AIExplanation,
    ) -> list[ReportInsight]:
        """
        Converts AI insights into report insights.
        """

        return [
            ReportInsight(
                category=insight.category,
                title=insight.title,
                description=insight.description,
            )
            for insight in explanation.insights
        ]