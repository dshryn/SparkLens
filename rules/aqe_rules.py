from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class AQERule(Rule):
    """
    Detects whether Adaptive Query Execution (AQE) is enabled.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.name != "AdaptiveSparkPlan":
                continue

            is_final_plan = any(
                "isFinalPlan=true" in argument
                for argument in operator.arguments
            )

            description = (
                "Adaptive Query Execution (AQE) is enabled. "
                "Spark can optimize the execution plan at runtime."
            )

            if not is_final_plan:
                description += (
                    " The final optimized plan has not yet been generated."
                )

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Adaptive Query Execution Detected",
                    description=description,
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                )
            )

        return findings