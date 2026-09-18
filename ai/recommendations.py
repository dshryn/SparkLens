from __future__ import annotations

from collections import defaultdict

from models.analysis_report import AnalysisReport
from models.enums import Severity


class RecommendationEngine:
    """
    Converts evidence-bearing AnalysisFindings into actionable
    recommendations.

    RecommendationEngine is the final evidence gatekeeper:

    - Positive findings never become recommendations.
    - Required operators never become optimization targets.
    - Generic recommendations cannot bypass structural evidence.
    - Every recommendation must originate from an AnalysisFinding.
    """

    _QUALITY_RULE_NAME = "ExecutionQualityRule"

    _RULE_RECOMMENDATIONS = {
        "BroadcastJoinRule": (
            "Spark selected a Broadcast Hash Join. Verify that the "
            "broadcast side remains sufficiently small as data volumes "
            "grow and continues to benefit from broadcasting."
        ),
        "ShuffleRule": (
            "This shuffle is not marked as required by any known query "
            "pattern. Review whether repartitioning, bucketing, or a "
            "broadcast join could avoid it."
        ),
        "ExchangeRule": (
            "This data exchange is not marked as required by any known "
            "query pattern. Review whether it can be avoided or "
            "consolidated."
        ),
        "AggregationRule": (
            "Ensure aggregation keys have suitable cardinality; consider "
            "whether a partial (map-side) aggregation could be introduced "
            "ahead of the shuffle."
        ),
        "PartitionRule": (
            "Review the partition count to avoid excessive task overhead."
        ),
        "SortRule": (
            "Verify that sorting is required and avoid redundant sort "
            "operations."
        ),
        "PerformanceRule": (
            "Review the execution plan for the potential bottleneck "
            "highlighted by SparkLens."
        ),
        "PipelineRule": (
            "Consider consolidating this long transformation pipeline "
            "where possible to improve maintainability."
        ),
    }

    _JOIN_STRATEGY_RECOMMENDATIONS = {
        "BroadcastHashJoin": (
            "Verify that the broadcast side remains sufficiently small "
            "as data volumes grow and continues to benefit from "
            "broadcasting."
        ),
        "SortMergeJoin": (
            "Review whether the sort-merge join is appropriate for the "
            "data sizes and join characteristics, and verify that the "
            "associated shuffles and sorts are justified."
        ),
        "ShuffleHashJoin": (
            "Review whether the shuffle hash join is appropriate for the "
            "data sizes and join characteristics, particularly the "
            "partitioning and build-side requirements."
        ),
    }

    _SEVERITY_PRIORITY = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
    }

    @classmethod
    def generate(
        cls,
        report: AnalysisReport,
    ) -> list[str]:

        required_operator_ids = (
            cls._collect_required_operator_ids(
                report
            )
        )

        positive_categories = (
            cls._collect_positive_categories(
                report
            )
        )

        eligible_findings = [
            finding
            for finding in report.findings
            if cls._is_eligible(
                finding,
                required_operator_ids,
                positive_categories,
                report,
            )
        ]

        grouped_findings: dict[
            tuple[str, str | None],
            list,
        ] = defaultdict(list)

        for finding in eligible_findings:

            join_strategy = finding.metadata.get(
                "join_strategy"
            )

            pattern = finding.metadata.get(
                "pattern"
            )

            if isinstance(
                join_strategy,
                str,
            ):

                group_key: str | None = (
                    join_strategy
                )

            elif isinstance(
                pattern,
                str,
            ):

                group_key = pattern

            else:

                group_key = None

            grouped_findings[
                (
                    finding.rule,
                    group_key,
                )
            ].append(
                finding
            )

        recommendations: list[
            tuple[int, str]
        ] = []

        for (
            rule,
            group_key,
        ), findings in grouped_findings.items():

            if (
                rule == "BroadcastJoinRule"
                and group_key
                in cls._JOIN_STRATEGY_RECOMMENDATIONS
            ):

                recommendation = (
                    cls._JOIN_STRATEGY_RECOMMENDATIONS[
                        group_key
                    ]
                )

            else:

                recommendation = (
                    cls._RULE_RECOMMENDATIONS.get(
                        rule
                    )
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
                    else rule.removesuffix(
                        "Rule"
                    )
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
                    "No optimization opportunities were identified. "
                    "The analyzed plan shows only expected, required, "
                    "or already-optimal execution patterns."
                )
            ]

        return [
            recommendation
            for _, recommendation
            in recommendations
        ]

    @classmethod
    def _collect_required_operator_ids(
        cls,
        report: AnalysisReport,
    ) -> set[int]:

        required_ids: set[int] = set()

        for finding in report.findings:

            if (
                finding.rule
                != cls._QUALITY_RULE_NAME
            ):
                continue

            if not finding.metadata.get(
                "required"
            ):
                continue

            operator_id = finding.metadata.get(
                "required_operator_id",
                finding.operator_id,
            )

            if isinstance(
                operator_id,
                int,
            ):

                required_ids.add(
                    operator_id
                )

        return required_ids

    @classmethod
    def _collect_positive_categories(
        cls,
        report: AnalysisReport,
    ) -> set[str]:

        categories: set[str] = set()

        for finding in report.findings:

            if (
                finding.rule
                != cls._QUALITY_RULE_NAME
            ):
                continue

            # A category only suppresses recommendations when the finding
            # explicitly establishes that the category is positive.
            if not finding.metadata.get(
                "positive"
            ):
                continue

            category = finding.metadata.get(
                "category"
            )

            if isinstance(
                category,
                str,
            ):

                categories.add(
                    category
                )

        return categories

    @classmethod
    def _is_eligible(
        cls,
        finding,
        required_operator_ids: set[int],
        positive_categories: set[str],
        report: AnalysisReport,
    ) -> bool:

        # Quality findings explain expected/required behavior and are never
        # directly converted into optimization recommendations.
        if (
            finding.rule
            == cls._QUALITY_RULE_NAME
        ):
            return False

        # Explicit positive evidence always blocks recommendation generation.
        if finding.metadata.get(
            "positive"
        ):

            return False

        # A finding attached directly to an operator already proven
        # structurally required cannot become an optimization target.
        if (
            finding.operator_id is not None
            and finding.operator_id
            in required_operator_ids
        ):

            return False

        # Once two-phase aggregation is established, generic aggregation
        # advice such as "consider introducing partial aggregation" is no
        # longer applicable.
        if (
            cls._normalize_rule_name(
                finding.rule
            )
            == "aggregationrule"
            and "two_phase_aggregation"
            in positive_categories
        ):

            return False

        # A PerformanceRule summary can have operator_id=None. If it
        # summarizes multiple shuffle operations, inspect the specific
        # shuffle ids attached to that finding. If every underlying shuffle
        # is already proven required, the summary must not generate generic
        # shuffle optimization advice.
        if (
            finding.rule
            == "PerformanceRule"
            and finding.title
            == "Multiple Shuffle Operations"
        ):

            shuffle_ids = (
                finding.metadata.get(
                    "shuffle_operator_ids"
                )
            )

            if (
                isinstance(
                    shuffle_ids,
                    list,
                )
                and shuffle_ids
                and all(
                    isinstance(
                        operator_id,
                        int,
                    )
                    and operator_id
                    in required_operator_ids
                    for operator_id
                    in shuffle_ids
                )
            ):

                return False

        return True

    @staticmethod
    def _normalize_rule_name(
        rule_name: str,
    ) -> str:

        return (
            rule_name
            .replace("_", "")
            .replace("-", "")
            .lower()
        )