from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator

from .base import Rule


class PipelineRule(Rule):
    """
    Detects pipelines of narrow transformations within a Spark stage.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for root in dag.root_nodes():

            pipeline_size = self._pipeline_size(
                dag,
                root,
            )

            if pipeline_size <= 1:
                continue

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Transformation Pipeline Detected",
                    description=(
                        f"A pipeline containing {pipeline_size} "
                        "operators executes without an intermediate "
                        "shuffle."
                    ),
                    severity=Severity.LOW,
                    operator_id=root.operator_id,
                )
            )

        return findings

    def _pipeline_size(
        self,
        dag: ExecutionDAG,
        operator: PhysicalOperator,
    ) -> int:

        if operator.operator_type == OperatorType.EXCHANGE:
            return 0

        size = 1

        for child in dag.children(operator.operator_id):
            size += self._pipeline_size(
                dag,
                child,
            )

        return size