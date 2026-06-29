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
                self._build_statistics(analysis),
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

        stats = analysis.statistics

        return ReportSection(
            title="Execution Overview",
            content=(
                f"Operators: {stats.operator_count}\n"
                f"Edges: {stats.edge_count}\n"
                f"Root Nodes: {stats.root_node_count}\n"
                f"Leaf Nodes: {stats.leaf_node_count}\n"
                f"Findings: {len(analysis.report.findings)}"
            ),
        )

    def _build_statistics(
        self,
        analysis: AnalysisResult,
    ) -> ReportSection:
        """
        Builds the execution statistics section.
        """

        stats = analysis.statistics

        return ReportSection(
            title="Execution Statistics",
            content=(
                f"Stages: {stats.stage_count}\n"
                f"Joins: {stats.join_count}\n"
                f"Broadcast Joins: {stats.broadcast_join_count}\n"
                f"Shuffles: {stats.shuffle_count}\n"
                f"Exchanges: {stats.exchange_count}\n"
                f"Aggregations: {stats.aggregate_count}\n"
                f"Sorts: {stats.sort_count}\n"
                f"Filters: {stats.filter_count}\n"
                f"Scans: {stats.scan_count}\n"
                f"Max Depth: {stats.max_depth}\n"
                f"Complexity: {stats.complexity} "
                f"({stats.complexity_score})"
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