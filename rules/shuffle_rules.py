from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class ShuffleRule(Rule):
    """
    Detects shuffle operations in the execution DAG.
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
                        "partitions and may become a performance bottleneck."
                    ),
                    severity=Severity.MEDIUM,
                    operator_id=operator.operator_id,
                )
            )

        return findings