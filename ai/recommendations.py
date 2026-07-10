from collections import defaultdict

from models.analysis_report import AnalysisReport
from models.enums import Severity


class RecommendationEngine:
    """
    Generates deterministic, evidence-aware optimization recommendations
    from SparkLens analysis findings.

    Recommendations are suppressed whenever ExecutionQualityRule has
    established that the underlying operator is required / already
    optimal (e.g. a shuffle required by a two-phase aggregation or a
    shuffle-based join, or an aggregation already using the two-phase
    strategy). No recommendation is ever generated without a
    corresponding finding as evidence.
    """

    _RULE_RECOMMENDATIONS = {
        "BroadcastJoinRule": (
            "Spark selected a Broadcast Hash Join. Verify that the broadcast side remains "
            "sufficiently small as data volumes grow and continues to benefit from broadcasting."
        ),
        "ShuffleRule": (
            "This shuffle is not marked as required by any known query pattern. "
            "Review whether repartitioning, bucketing, or a broadcast join could "
            "avoid it."
        ),
        "ExchangeRule": (
            "This data exchange is not marked as required by any known query "
            "pattern. Review whether it can be avoided or consolidated."
        ),
        "AggregationRule": (
            "Ensure aggregation keys have suitable cardinality; consider whether "
            "a partial (map-side) aggregation could be introduced ahead of the "
            "shuffle."
        ),
        "PartitionRule": (
            "Review the partition count to avoid excessive task overhead."
        ),
        "SortRule": (
            "Verify that sorting is required and avoid redundant sort operations."
        ),
        "PerformanceRule": (
            "Review the execution plan for the potential bottleneck highlighted "
            "by SparkLens."
        ),
        "PipelineRule": (
            "Consider consolidating this long transformation pipeline where "
            "possible to improve maintainability."
        ),
    }

    _JOIN_STRATEGY_RECOMMENDATIONS = {
        "BroadcastHashJoin": (
            "Spark selected a Broadcast Hash Join. "
            "This is typically an efficient strategy when one side of the join is small. "
            "Verify that the broadcast side remains within Spark's broadcast threshold as data grows."
        ),
        "SortMergeJoin": (
            "Spark selected a Sort Merge Join, which requires a shuffle to "
            "co-locate join keys. If one side of the join is small enough, "
            "consider whether a broadcast join would avoid the shuffle."
        ),
        "ShuffleHashJoin": (
            "Spark selected a Shuffle Hash Join, which requires a shuffle to "
            "co-locate join keys. Review join-key distribution and, if one "
            "side is small enough, consider a broadcast join instead."
        ),
    }

    _SEVERITY_PRIORITY = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }

    _QUALITY_RULE_NAME = "ExecutionQualityRule"

    @classmethod
    def generate(cls, report: AnalysisReport) -> list[str]:
        """
        Generate deterministic optimization recommendations.

        Recommendations are:
        - Evidence-aware: suppressed when ExecutionQualityRule shows the
          underlying operator/pattern is required or already optimal.
        - Ordered by highest finding severity.
        - Deduplicated by rule and join strategy.
        - Aggregated when multiple findings originate from the same rule.
        """

        required_operator_ids = cls._collect_required_operator_ids(report)
        positive_categories = cls._collect_positive_categories(report)

        eligible_findings = [
            finding
            for finding in report.findings
            if cls._is_eligible(
                finding,
                required_operator_ids,
                positive_categories,
            )
        ]

        grouped_findings: dict[tuple[str, str | None], list] = defaultdict(list)

        for finding in eligible_findings:

            join_strategy = finding.metadata.get("join_strategy")
            pattern = finding.metadata.get("pattern")

            if isinstance(join_strategy, str):
                group_key: str | None = join_strategy
            elif isinstance(pattern, str):
                group_key = pattern
            else:
                group_key = None

            grouped_findings[(finding.rule, group_key)].append(finding)

        recommendations: list[tuple[int, str]] = []

        for (rule, group_key), findings in grouped_findings.items():

            if (
                rule == "BroadcastJoinRule"
                and group_key in cls._JOIN_STRATEGY_RECOMMENDATIONS
            ):
                recommendation = cls._JOIN_STRATEGY_RECOMMENDATIONS[
                    group_key
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
                    group_key
                    if group_key
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
                    "No optimization recommendations were generated. "
                    "The analyzed plan shows only expected execution costs "
                    "and/or already-optimal patterns."
                )
            ]

        return [
            recommendation
            for _, recommendation in recommendations
        ]

    @classmethod
    def _collect_required_operator_ids(
        cls,
        report: AnalysisReport,
    ) -> set[int]:
        """
        Operator ids that ExecutionQualityRule has established as required
        (e.g. a shuffle needed by a two-phase aggregation or a shuffle-based
        join). Recommendations must never target these operators.
        """

        required_ids: set[int] = set()

        for finding in report.findings:

            if finding.rule != cls._QUALITY_RULE_NAME:
                continue

            if not finding.metadata.get("required"):
                continue

            operator_id = finding.metadata.get(
                "required_operator_id",
                finding.operator_id,
            )

            if isinstance(operator_id, int):
                required_ids.add(operator_id)

        return required_ids

    @classmethod
    def _collect_positive_categories(
        cls,
        report: AnalysisReport,
    ) -> set[str]:
        """
        Positive pattern categories established by ExecutionQualityRule
        (e.g. "two_phase_aggregation"). Used to suppress recommendations
        for patterns that are already optimal.
        """

        categories: set[str] = set()

        for finding in report.findings:

            if finding.rule != cls._QUALITY_RULE_NAME:
                continue

            category = finding.metadata.get("category")

            if isinstance(category, str):
                categories.add(category)

        return categories

    @classmethod
    def _is_eligible(
        cls,
        finding,
        required_operator_ids: set[int],
        positive_categories: set[str],
    ) -> bool:
        """
        Determines whether a finding may still produce a recommendation
        once evidence of required/optimal patterns is taken into account.
        """

        # Never generate recommendations directly from quality findings;
        # they are explanatory, not actionable.
        if finding.rule == cls._QUALITY_RULE_NAME:
            return False

        # Explicitly positive findings from any rule are never actionable.
        if finding.metadata.get("positive"):
            return False

        # Suppress ANY recommendation targeting an operator that
        # ExecutionQualityRule has established as required, regardless of
        # which rule produced the finding (e.g. ShuffleRule, ExchangeRule,
        # PartitionRule, SortRule, ...). A required operator is required
        # no matter which downstream rule happens to flag it.
        if finding.operator_id in required_operator_ids:
            return False

        normalized_rule = cls._normalize_rule_name(finding.rule)

        # Suppress aggregation recommendations if the aggregation already
        # follows the optimal two-phase strategy.
        if normalized_rule == "AggregationRule":

            if "two_phase_aggregation" in positive_categories:
                return False

        return True

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