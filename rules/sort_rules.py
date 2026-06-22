from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class SortRule(Rule):
    """
    Detects sort operations in the execution DAG.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.SORT:
                continue

            arguments = " ".join(operator.arguments)

            description = (
                "Spark sorts the dataset before downstream processing."
            )

            if "ASC" in arguments:
                description += " Sort order: Ascending."

            elif "DESC" in arguments:
                description += " Sort order: Descending."

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Sort Operation Detected",
                    description=description,
                    severity=Severity.MEDIUM,
                    operator_id=operator.operator_id,
                )
            )

        return findings