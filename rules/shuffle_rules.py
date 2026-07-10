from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class ShuffleRule(Rule):
    """
    Detects shuffle operations in the execution DAG.

    This rule only records the raw observation that a shuffle exists at a
    given operator. It intentionally does NOT judge whether the shuffle is
    required, expected, or unnecessary -- that classification is the sole
    responsibility of ExecutionQualityRule, whose "required": True /
    "positive": True metadata is used by RecommendationEngine to decide
    whether this finding is allowed to produce an optimization
    recommendation. Without matching ExecutionQualityRule evidence, this
    finding remains a candidate optimization opportunity; with it, the
    recommendation is suppressed.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.EXCHANGE:
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Shuffle Detected",
                    description=(
                        "A shuffle exchange redistributes data across "
                        "partitions. Whether this shuffle is required, "
                        "expected, or an optimization opportunity is "
                        "determined by ExecutionQualityRule's evidence for "
                        "this operator."
                    ),
                    severity=Severity.MEDIUM,
                    operator_id=operator.operator_id,
                )
            )

        return findings