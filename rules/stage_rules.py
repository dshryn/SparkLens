from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class StageRule(Rule):
    """
    Detects Spark stage boundaries.

    SparkLens defines an estimated stage count as:

        1 initial stage + number of shuffle Exchange operators

    Wide transformations such as aggregation do not themselves create an
    additional stage. The Exchange that separates the stages is the actual
    shuffle boundary.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        exchange_count = 0

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.EXCHANGE:
                continue

            exchange_count += 1

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Stage Boundary Detected",
                    description=(
                        "This Exchange represents a shuffle boundary "
                        "between Spark execution stages."
                    ),
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                )
            )

        stage_count = 1 + exchange_count

        findings.append(
            AnalysisFinding(
                rule=self.__class__.__name__,
                title="Estimated Stage Count",
                description=(
                    f"SparkLens estimates {stage_count} execution "
                    f"stage(s) from {exchange_count} shuffle "
                    f"boundary Exchange operator(s)."
                ),
                severity=Severity.LOW,
                metadata={
                    "positive": True,
                    "category": "stage_count",
                    "stage_count": stage_count,
                    "shuffle_boundary_count": exchange_count,
                },
            )
        )

        return findings