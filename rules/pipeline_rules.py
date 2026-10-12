from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator

from .base import Rule


class PipelineRule(Rule):
    """
    Reports a narrow pipeline only when the ENTIRE plan has no Exchange or
    BroadcastExchange, i.e. every operator is fused into one stage.
    """

    _TRIVIAL_THRESHOLD = 1
    _COMPLEXITY_THRESHOLD = 8
    _BOUNDARY_TYPES = (
        OperatorType.EXCHANGE,
        OperatorType.BROADCAST_EXCHANGE,
    )

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        if any(
            operator.operator_type in self._BOUNDARY_TYPES
            for operator in dag.operators.values()
        ):
            return []

        roots = dag.root_nodes()

        pipeline_size = sum(
            self._pipeline_size(dag, root)
            for root in roots
        )

        if pipeline_size <= self._TRIVIAL_THRESHOLD or not roots:
            return []

        root_id = roots[0].operator_id

        if pipeline_size >= self._COMPLEXITY_THRESHOLD:

            return [
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Complex Transformation Pipeline",
                    description=(
                        f"{pipeline_size} narrow operators are fused into "
                        "one long pipeline with no shuffle."
                    ),
                    severity=Severity.MEDIUM,
                    operator_id=root_id,
                    metadata={
                        "positive": False,
                        "category": "complex_pipeline",
                        "pipeline_size": pipeline_size,
                    },
                )
            ]

        if any(
            any(
                token in operator.name.lower()
                for token in (
                    "sort",
                    "coalesce",
                    "cartesian",
                    "takeordered",
                    "nestedloop",
                    "window",
                )
            )
            for operator in dag.operators.values()
        ):
            return []

        return [
            AnalysisFinding(
                rule=self.__class__.__name__,
                title="Narrow Pipeline",
                description=(
                    "All operators are narrow and are fused into a single "
                    "pipeline with no shuffle."
                ),
                severity=Severity.LOW,
                operator_id=root_id,
                metadata={
                    "positive": True,
                    "category": "efficient_pipeline",
                    "pipeline_size": pipeline_size,
                },
            )
        ]

    def _pipeline_size(
        self,
        dag: ExecutionDAG,
        operator: PhysicalOperator,
    ) -> int:

        if operator.operator_type in self._BOUNDARY_TYPES:
            return 0

        size = 1

        for child in dag.children(operator.operator_id):
            size += self._pipeline_size(dag, child)

        return size
