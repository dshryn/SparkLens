from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator

from .base import Rule


class PipelineRule(Rule):
    """
    Detects pipelines of narrow transformations within a Spark stage.

    Small pipelines are not reported at all.
    Reasonably sized pipelines are reported as a POSITIVE finding
    (an efficient transformation pipeline with no intermediate shuffle).
    Only pipelines that are excessively long are reported as a real
    complexity concern.
    """

    _TRIVIAL_THRESHOLD = 2
    _COMPLEXITY_THRESHOLD = 8

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

            if pipeline_size <= self._TRIVIAL_THRESHOLD:
                continue

            if pipeline_size >= self._COMPLEXITY_THRESHOLD:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Complex Transformation Pipeline",
                        description=(
                            f"A pipeline containing {pipeline_size} "
                            "operators executes without an intermediate "
                            "shuffle. Its length may make the plan harder "
                            "to reason about and could indicate "
                            "opportunities to consolidate transformations."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=root.operator_id,
                        metadata={
                            "positive": False,
                            "category": "complex_pipeline",
                            "pipeline_size": pipeline_size,
                        },
                    )
                )

            else:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Efficient Transformation Pipeline",
                        description=(
                            f"A pipeline containing {pipeline_size} "
                            "operators executes without an intermediate "
                            "shuffle, avoiding unnecessary data movement "
                            "between operators."
                        ),
                        severity=Severity.LOW,
                        operator_id=root.operator_id,
                        metadata={
                            "positive": True,
                            "category": "efficient_pipeline",
                            "pipeline_size": pipeline_size,
                        },
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