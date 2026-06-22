from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class StageRule(Rule):
    """
    Detects Spark stage boundaries.

    Every shuffle exchange sink represents the end of one stage.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        stage_count = 1

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.EXCHANGE:
                continue

            if "shuffleexchangesink" not in operator.name.lower():
                continue

            stage_count += 1

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Stage Boundary Detected",
                    description=(
                        "A shuffle exchange creates a new Spark stage."
                    ),
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                )
            )

        findings.append(
            AnalysisFinding(
                rule=self.__class__.__name__,
                title="Estimated Stage Count",
                description=(
                    f"The execution plan is expected to contain "
                    f"{stage_count} Spark stage(s)."
                ),
                severity=Severity.LOW,
            )
        )

        return findings