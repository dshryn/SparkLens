from __future__ import annotations

import logging

from analyzer.dag_builder import DAGBuilder
from analyzer.extractor import FormattedPlanExtractor
from analyzer.normalizer import PlanNormalizer
from analyzer.parser import PlanParser

from models.analysis_result import AnalysisResult

from rules.aqe_rules import AQERule
from rules.aggregation_rules import AggregationRule
from rules.engine import RuleEngine
from rules.exchange_rules import ExchangeRule
from rules.join_rules import BroadcastJoinRule
from rules.partition_rules import PartitionRule
from rules.performance_rules import PerformanceRule
from rules.pipeline_rules import PipelineRule
from rules.shuffle_rules import ShuffleRule
from rules.sort_rules import SortRule
from rules.stage_rules import StageRule


logger = logging.getLogger(__name__)


class SparkAnalyzer:
    """
    High-level orchestration entry point for SparkLens.
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

        result = AnalysisResult(
            dag=dag,
            report=report,
        )

        logger.info("Analysis pipeline completed successfully.")

        return result

    @staticmethod
    def _default_rule_engine() -> RuleEngine:
        """
        Create the default SparkLens rule engine.
        """

        return RuleEngine(
            [
                BroadcastJoinRule(),
                ShuffleRule(),
                ExchangeRule(),
                PartitionRule(),
                AggregationRule(),
                SortRule(),
                AQERule(),
                StageRule(),
                PerformanceRule(),
                PipelineRule(),
            ]
        )