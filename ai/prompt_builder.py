from collections import Counter

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
            operator_count=len(result.dag.operators),
            execution_statistics=execution_statistics,
            execution_flow=execution_flow,
            findings=findings,
            recommendations="\n".join(
                f"- {recommendation}"
                for recommendation in recommendations
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

        dag = result.dag
        findings = result.report.findings

        operator_type_counts = Counter(
            operator.operator_type.name
            for operator in dag.operators.values()
        )

        severity_counts = Counter(
            finding.severity
            for finding in findings
        )

        lines = [
            f"Operators: {len(dag.operators)}",
            f"Edges: {len(dag.edges)}",
            f"Root Nodes: {len(dag.root_nodes())}",
            f"Leaf Nodes: {len(dag.leaf_nodes())}",
            "",
            "Operator Types:",
        ]

        for operator_type in sorted(operator_type_counts):
            lines.append(
                f"- {operator_type}: {operator_type_counts[operator_type]}"
            )

        lines.extend([
            "",
            "Severity Summary:",
        ])

        for severity in (
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
        ):
            lines.append(
                f"- {severity.name}: {severity_counts.get(severity, 0)}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_execution_flow(result: AnalysisResult) -> str:
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
    def _format_findings(result: AnalysisResult) -> str:
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
                }.get(finding.severity, 99),
                finding.operator_id
                if finding.operator_id is not None
                else -1,
            ),
        )

        if not findings:
            return "No significant findings."

        formatted = []

        for index, finding in enumerate(findings, start=1):

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
                    f"   Operator: #{operator.operator_id} {operator.name}"
                )

            lines.append(f"   {finding.description}")

            if finding.metadata:
                lines.append("   Metadata:")

                for key, value in sorted(finding.metadata.items()):
                    lines.append(
                        f"      - {key}: {value}"
                    )

            formatted.append("\n".join(lines))

        return "\n\n".join(formatted)