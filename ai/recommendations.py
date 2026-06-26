from collections import defaultdict

from models.analysis_report import AnalysisReport
from models.enums import Severity


class RecommendationEngine:
    """
    Generates deterministic optimization recommendations
    from SparkLens analysis findings.
    """

    _RULE_RECOMMENDATIONS = {
        "BroadcastJoinRule": (
            "Consider broadcasting the smaller dataset to reduce shuffle overhead."
        ),
        "ShuffleRule": (
            "Review partitioning strategy to minimize expensive shuffle operations."
        ),
        "ExchangeRule": (
            "Avoid unnecessary data exchanges by reducing repartitioning where possible."
        ),
        "AggregationRule": (
            "Ensure aggregation keys have suitable cardinality and consider pre-aggregation."
        ),
        "PartitionRule": (
            "Review the partition count to avoid data skew or excessive task overhead."
        ),
        "SortRule": (
            "Verify that sorting is required and avoid redundant sort operations."
        ),
        "AQERule": (
            "Adaptive Query Execution is enabled. Ensure Spark can leverage runtime optimizations."
        ),
        "PerformanceRule": (
            "Review the execution plan for potential bottlenecks highlighted by SparkLens."
        ),
        "PipelineRule": (
            "Simplify complex execution pipelines where possible to improve maintainability."
        ),
    }

    _SEVERITY_PRIORITY = {
        Severity.HIGH: 0,
        Severity.MEDIUM: 1,
        Severity.LOW: 2,
    }

    @classmethod
    def generate(cls, report: AnalysisReport) -> list[str]:
        """
        Generate deterministic optimization recommendations.

        Recommendations are:
        - Ordered by highest finding severity.
        - Deduplicated by rule.
        - Aggregated when multiple findings originate from the same rule.
        """

        grouped_findings: dict[str, list] = defaultdict(list)

        for finding in report.findings:
            normalized_rule = cls._normalize_rule_name(
                finding.rule
            )
            grouped_findings[normalized_rule].append(finding)

        recommendations: list[tuple[int, str]] = []

        for rule, findings in grouped_findings.items():

            recommendation = cls._RULE_RECOMMENDATIONS.get(rule)

            if recommendation is None:
                continue

            highest_severity = min(
                cls._SEVERITY_PRIORITY[finding.severity]
                for finding in findings
            )

            count = len(findings)

            if count == 1:
                message = recommendation
            else:
                message = (
                    f"{count} findings were detected by "
                    f"{rule.removesuffix('Rule')}. "
                    f"{recommendation}"
                )

            recommendations.append(
                (
                    highest_severity,
                    message,
                )
            )

        recommendations.sort(
            key=lambda item: item[0]
        )

        if not recommendations:
            return [
                (
                    "No optimization recommendations were generated "
                    "from the current analysis."
                )
            ]

        return [
            recommendation
            for _, recommendation in recommendations
        ]

    @staticmethod
    def _normalize_rule_name(
        rule: str,
    ) -> str:
        """
        Normalizes rule names to the canonical Rule class name.

        Examples:
            Shuffle -> ShuffleRule
            ShuffleRule -> ShuffleRule
            Broadcast Join -> BroadcastJoinRule
            BroadcastJoinRule -> BroadcastJoinRule
        """

        if rule.endswith("Rule"):
            return rule

        return (
            rule.replace(" ", "")
            + "Rule"
        )