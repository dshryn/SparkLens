from __future__ import annotations

import logging

from analyzer.dag_builder import DAGBuilder
from analyzer.extractor import FormattedPlanExtractor
from analyzer.normalizer import PlanNormalizer
from analyzer.parser import PlanParser

from models.analysis_result import AnalysisResult
from models.execution_dag import ExecutionDAG
from models.execution_statistics import ExecutionStatistics
from models.analysis_report import AnalysisReport
from models.enums import OperatorType
from models.enums import Severity
from models.enums import TransformationType

from rules.aggregation_rules import AggregationRule
from rules.engine import RuleEngine
from rules.exchange_rules import ExchangeRule
from rules.join_rules import BroadcastJoinRule
from rules.partition_rules import PartitionRule
from rules.performance_rules import PerformanceRule
from rules.pipeline_rules import PipelineRule
from rules.quality_rules import ExecutionQualityRule
from rules.shuffle_rules import ShuffleRule
from rules.sort_rules import SortRule
from rules.stage_rules import StageRule


logger = logging.getLogger(__name__)


class SparkAnalyzer:
    """
    High-level orchestration entry point for SparkLens.

    NOTE: AQERule has been removed from the default rule set. AQE detection
    is now owned exclusively by ExecutionQualityRule ("AQE Enabled"), which
    prevents the previous duplicate finding ("AQE Enabled" +
    "Adaptive Query Execution Detected") for the same AdaptiveSparkPlan
    operator. RuleEngine also deduplicates defensively at the report level
    in case a custom rule set still registers both.
    """

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
    ) -> None:

        self._extractor = FormattedPlanExtractor()
        self._normalizer = PlanNormalizer()
        self._parser = PlanParser()
        self._builder = DAGBuilder()

        self._rule_engine = (
            rule_engine
            if rule_engine is not None
            else self._default_rule_engine()
        )

    def analyze(
        self,
        dataframe,
    ) -> AnalysisResult:
        """
        Analyze a Spark DataFrame.
        """

        logger.info("Starting DataFrame analysis.")

        plan = self._extractor.extract(
            dataframe
        )

        logger.info(
            "Execution plan extracted (%d characters).",
            len(plan),
        )

        return self.analyze_plan(
            plan
        )

    def analyze_plan(
        self,
        plan: str,
    ) -> AnalysisResult:
        """
        Analyze an already extracted Spark execution plan.
        """

        logger.info("Starting execution plan analysis.")

        normalized_plan = self._normalizer.normalize(
            plan
        )

        logger.info(
            "Plan normalized."
        )

        parsed_plan = self._parser.parse(
            normalized_plan
        )

        logger.info(
            "Plan parsed (%d operators, %d edges).",
            len(parsed_plan.operators),
            len(parsed_plan.edges),
        )

        dag = self._builder.build(
            parsed_plan
        )

        logger.info(
            "Execution DAG constructed (%d operators, %d edges).",
            len(dag.operators),
            len(dag.edges),
        )

        report = self._rule_engine.run(
            dag
        )

        logger.info(
            "Rule engine completed (%d findings).",
            len(report.findings),
        )

        statistics = self._compute_statistics(
            dag,
            report,
        )

        result = AnalysisResult(
            dag=dag,
            report=report,
            statistics=statistics,
        )

        logger.info("Analysis pipeline completed successfully.")

        return result

    def _compute_statistics(
        self,
        dag: ExecutionDAG,
        report: AnalysisReport,
    ) -> ExecutionStatistics:

        stats = ExecutionStatistics()

        stats.operator_count = len(dag.operators)
        stats.edge_count = len(dag.edges)

        stats.root_node_count = len(
            dag.root_nodes()
        )

        stats.leaf_node_count = len(
            dag.leaf_nodes()
        )

        operator_types: dict[str, int] = {}
        transformations: dict[str, int] = {}
        join_strategies: dict[str, int] = {}

        max_depth = 0
        wide_transformation_count = 0

        for operator in dag.operators.values():

            max_depth = max(
                max_depth,
                operator.depth,
            )

            operator_name = operator.operator_type.value

            operator_types[operator_name] = (
                operator_types.get(
                    operator_name,
                    0,
                )
                + 1
            )

            transformation = (
                operator.transformation.value
            )

            transformations[transformation] = (
                transformations.get(
                    transformation,
                    0,
                )
                + 1
            )

            match operator.operator_type:

                case OperatorType.EXCHANGE:
                    stats.exchange_count += 1
                    stats.shuffle_count += 1

                case OperatorType.BROADCAST_EXCHANGE:
                    stats.exchange_count += 1

                case OperatorType.BROADCAST_HASH_JOIN:
                    stats.join_count += 1
                    stats.broadcast_join_count += 1

                    join_strategies[
                        operator.operator_type.value
                    ] = (
                        join_strategies.get(
                            operator.operator_type.value,
                            0,
                        )
                        + 1
                    )

                case (
                    OperatorType.SORT_MERGE_JOIN
                    | OperatorType.SHUFFLE_HASH_JOIN
                ):
                    stats.join_count += 1

                    join_strategies[
                        operator.operator_type.value
                    ] = (
                        join_strategies.get(
                            operator.operator_type.value,
                            0,
                        )
                        + 1
                    )

                case (
                    OperatorType.HASH_AGGREGATE
                    | OperatorType.SORT_AGGREGATE
                ):
                    stats.aggregate_count += 1

                case OperatorType.SORT:
                    stats.sort_count += 1

                case OperatorType.FILTER:
                    stats.filter_count += 1

                case OperatorType.FILE_SCAN:
                    stats.scan_count += 1

            if (
                operator.transformation
                == TransformationType.WIDE
            ):
                wide_transformation_count += 1

        # Stage count is defined as: one initial stage, plus one additional
        # stage for every wide (shuffle-boundary) transformation. This is
        # the single, canonical stage-estimation formula for the analyzer.
        # Any rule that reports a stage estimate (e.g. StageRule) MUST use
        # this same value via `stats.stage_count` rather than recomputing
        # its own count, so that statistics and findings never disagree.
        stats.stage_count = 1 + wide_transformation_count

        stats.max_depth = max_depth

        stats.operator_types = operator_types
        stats.transformations = transformations
        stats.join_strategies = join_strategies

        for finding in report.findings:

            match finding.severity:

                case Severity.CRITICAL:
                    stats.critical_findings += 1

                case Severity.HIGH:
                    stats.high_findings += 1

                case Severity.MEDIUM:
                    stats.medium_findings += 1

                case Severity.LOW:
                    stats.low_findings += 1

        score = (
            stats.operator_count * 0.25
            + stats.join_count * 4
            + stats.shuffle_count * 5
            + stats.exchange_count * 3
            + stats.max_depth
        )

        stats.complexity_score = round(
            score,
            2,
        )

        if score < 10:
            stats.complexity = "LOW"

        elif score < 20:
            stats.complexity = "MEDIUM"

        elif score < 35:
            stats.complexity = "HIGH"

        else:
            stats.complexity = "VERY_HIGH"

        return stats

    @staticmethod
    def _default_rule_engine() -> RuleEngine:
        """
        Create the default SparkLens rule engine.

        AQERule is intentionally NOT registered here: AQE detection is
        owned exclusively by ExecutionQualityRule to avoid duplicate
        findings for the same AdaptiveSparkPlan operator.
        """

        return RuleEngine(
            [
                BroadcastJoinRule(),
                ShuffleRule(),
                ExchangeRule(),
                PartitionRule(),
                AggregationRule(),
                SortRule(),
                StageRule(),
                PerformanceRule(),
                PipelineRule(),
                ExecutionQualityRule(),
            ]
        )