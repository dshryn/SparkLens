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
            "Spark selected a Broadcast Hash Join. Verify that the broadcast side remains "
            "sufficiently small as data volumes grow and continues to benefit from broadcasting."
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

    _JOIN_STRATEGY_RECOMMENDATIONS = {
        "BroadcastHashJoin": (
            "Spark selected a Broadcast Hash Join. "
            "This is typically an efficient strategy when one side of the join is small. "
            "Verify that the broadcast side remains within Spark's broadcast threshold as data grows."
        ),
        "SortMergeJoin": (
            "Spark selected a Sort Merge Join. "
            "This strategy generally incurs shuffle and sort overhead. "
            "Review whether partitioning can be improved or whether one side of the join could be broadcast."
        ),
        "ShuffleHashJoin": (
            "Spark selected a Shuffle Hash Join. "
            "Review join-key distribution and partitioning to minimize shuffle overhead."
        ),
    }

    _SEVERITY_PRIORITY = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }

    @classmethod
    def generate(cls, report: AnalysisReport) -> list[str]:
        """
        Generate deterministic optimization recommendations.

        Recommendations are:
        - Ordered by highest finding severity.
        - Deduplicated by rule and join strategy.
        - Aggregated when multiple findings originate from the same rule.
        """

        grouped_findings: dict[tuple[str, str | None], list] = defaultdict(list)

        for finding in report.findings:

            normalized_rule = cls._normalize_rule_name(
                finding.rule
            )

            join_strategy = finding.metadata.get(
                "join_strategy"
            )

            grouped_findings[
                (
                    normalized_rule,
                    join_strategy,
                )
            ].append(finding)

        recommendations: list[tuple[int, str]] = []

        for (rule, join_strategy), findings in grouped_findings.items():

            if (
                rule == "BroadcastJoinRule"
                and join_strategy in cls._JOIN_STRATEGY_RECOMMENDATIONS
            ):
                recommendation = cls._JOIN_STRATEGY_RECOMMENDATIONS[
                    join_strategy
                ]
            else:
                recommendation = cls._RULE_RECOMMENDATIONS.get(
                    rule
                )

            if recommendation is None:
                continue

            highest_severity = min(
                cls._SEVERITY_PRIORITY.get(
                    finding.severity,
                    99,
                )
                for finding in findings
            )

            count = len(findings)

            if count > 1:

                subject = (
                    join_strategy
                    if join_strategy
                    else rule.removesuffix("Rule")
                )

                recommendation = (
                    f"{count} {subject} findings were detected. "
                    f"{recommendation}"
                )

            recommendations.append(
                (
                    highest_severity,
                    recommendation,
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