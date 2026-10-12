from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class LimitRule(Rule):
    """Detects unions."""

    def apply(self, dag: ExecutionDAG) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():
            if operator.name != "Union":
                continue

            input_count = len(dag.children(operator.operator_id))
            if input_count < 2:
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Union Detected",
                    description=(
                        f"{input_count} inputs are combined with a Union, "
                        "which concatenates their partitions without moving "
                        "data."
                    ),
                    severity=Severity.LOW,
                    operator_id=operator.operator_id,
                )
            )

        return findings
