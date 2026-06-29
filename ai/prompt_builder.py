from ai.models import AIPrompt
from ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ai.recommendations import RecommendationEngine
from models.analysis_result import AnalysisResult
from models.enums import Severity


class PromptBuilder:
    """
    Builds LLM-ready prompts from deterministic SparkLens analysis.
    """

    @staticmethod
    def build(result: AnalysisResult) -> AIPrompt:
        """
        Builds a complete prompt from an AnalysisResult.
        """

        execution_statistics = PromptBuilder._format_execution_statistics(result)

        execution_flow = PromptBuilder._format_execution_flow(result)

        findings = PromptBuilder._format_findings(result)

        recommendations = RecommendationEngine.generate(result.report)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            operator_count=result.statistics.operator_count,
            execution_statistics=execution_statistics,
            execution_flow=execution_flow,
            findings=findings,
            recommendations="\n".join(
                f"- {recommendation}" for recommendation in recommendations
            ),
        )

        return AIPrompt(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    @staticmethod
    def _format_execution_statistics(
        result: AnalysisResult,
    ) -> str:
        """
        Formats deterministic execution statistics for the LLM.
        """

        stats = result.statistics

        lines = [
            f"Operators: {stats.operator_count}",
            f"Edges: {stats.edge_count}",
            f"Root Nodes: {stats.root_node_count}",
            f"Leaf Nodes: {stats.leaf_node_count}",
            f"Stages: {stats.stage_count}",
            f"Joins: {stats.join_count}",
            f"Broadcast Joins: {stats.broadcast_join_count}",
            f"Shuffles: {stats.shuffle_count}",
            f"Exchanges: {stats.exchange_count}",
            f"Aggregations: {stats.aggregate_count}",
            f"Sorts: {stats.sort_count}",
            f"Filters: {stats.filter_count}",
            f"Scans: {stats.scan_count}",
            f"Max Depth: {stats.max_depth}",
            (f"Complexity: " f"{stats.complexity} " f"({stats.complexity_score})"),
            "",
            "Operator Types:",
        ]

        for operator_type in sorted(stats.operator_types):
            lines.append(
                f"- {operator_type}: " f"{stats.operator_types[operator_type]}"
            )

        lines.extend(
            [
                "",
                "Transformation Types:",
            ]
        )

        for transformation in sorted(stats.transformations):
            lines.append(
                f"- {transformation}: " f"{stats.transformations[transformation]}"
            )

        lines.extend(
            [
                "",
                "Severity Summary:",
                f"- CRITICAL: {stats.critical_findings}",
                f"- HIGH: {stats.high_findings}",
                f"- MEDIUM: {stats.medium_findings}",
                f"- LOW: {stats.low_findings}",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_execution_flow(
        result: AnalysisResult,
    ) -> str:
        """
        Formats the execution DAG into a readable execution flow.
        """

        operators = result.dag.topological_order()

        if not operators:
            return "No operators found."

        return "\n".join(
            (
                f"- #{operator.operator_id} "
                f"{operator.name} "
                f"({operator.operator_type.name})"
            )
            for operator in operators
        )

    @staticmethod
    def _format_findings(
        result: AnalysisResult,
    ) -> str:
        """
        Formats deterministic findings for inclusion in the prompt.
        """

        findings = sorted(
            result.report.findings,
            key=lambda finding: (
                {
                    Severity.HIGH: 0,
                    Severity.MEDIUM: 1,
                    Severity.LOW: 2,
                    Severity.CRITICAL: -1,
                }.get(finding.severity, 99),
                finding.operator_id if finding.operator_id is not None else -1,
            ),
        )

        if not findings:
            return "No significant findings."

        formatted: list[str] = []

        for index, finding in enumerate(
            findings,
            start=1,
        ):

            operator = (
                result.dag.get_operator(finding.operator_id)
                if finding.operator_id is not None
                else None
            )

            lines = [
                f"{index}. [{finding.severity.name}] {finding.title}",
                f"   Rule: {finding.rule}",
            ]

            if operator is not None:
                lines.append(
                    f"   Operator: " f"#{operator.operator_id} " f"{operator.name}"
                )

            lines.append(f"   {finding.description}")

            if finding.metadata:
                lines.append("   Metadata:")

                for key, value in sorted(finding.metadata.items()):
                    lines.append(f"      - {key}: {value}")

            formatted.append("\n".join(lines))

        return "\n\n".join(formatted)
