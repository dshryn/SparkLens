from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class BroadcastJoinRule(Rule):
    """
    Detects BroadcastHashJoin operators.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if (
                operator.operator_type
                != OperatorType.BROADCAST_HASH_JOIN
            ):
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Broadcast Hash Join Detected",
                    description=(
                        "Spark selected a Broadcast Hash Join "
                        "for this operator."
                    ),
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                )
            )

        return findings