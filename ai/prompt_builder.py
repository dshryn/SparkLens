from ai.models import AIPrompt
from ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ai.recommendations import RecommendationEngine
from models.analysis_result import AnalysisResult


class PromptBuilder:
    """
    Builds LLM-ready prompts from deterministic SparkLens analysis.
    """

    @staticmethod
    def build(result: AnalysisResult) -> AIPrompt:
        """
        Builds a complete prompt from an AnalysisResult.
        """
        execution_flow = PromptBuilder._format_execution_flow(result)
        findings = PromptBuilder._format_findings(result)

        recommendations = RecommendationEngine.generate(result.report)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            operator_count=len(result.dag.operators),
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
    def _format_execution_flow(result: AnalysisResult) -> str:
        """
        Formats the execution DAG into a readable execution flow.
        """
        operators = result.dag.topological_order()

        if not operators:
            return "No operators found."

        return "\n".join(
            f"- {operator.name}"
            for operator in operators
        )

    @staticmethod
    def _format_findings(result: AnalysisResult) -> str:
        """
        Formats analysis findings for inclusion in the prompt.
        """
        findings = result.report.findings

        if not findings:
            return "No significant findings."

        formatted = []

        for index, finding in enumerate(findings, start=1):
            formatted.append(
                "\n".join(
                    [
                        f"{index}. [{finding.severity.name}] {finding.title}",
                        f"   Rule: {finding.rule}",
                        f"   {finding.description}",
                    ]
                )
            )

        return "\n\n".join(formatted)