from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import Severity
from models.execution_dag import ExecutionDAG

from .base import Rule
from .shuffle_utils import is_shuffle_boundary


class StageRule(Rule):
    """
    Detects Spark stage boundaries.

    Estimated stage count = 1 initial stage + number of shuffle boundaries.
    The count sentence deliberately states ONE number (the stage count);
    the boundary count lives in metadata.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        boundary_count = 0

        for operator in dag.operators.values():

            if not is_shuffle_boundary(operator):
                continue

            boundary_count += 1

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

        stage_count = 1 + boundary_count
        noun = "stage" if stage_count == 1 else "stages"

        findings.append(
            AnalysisFinding(
                rule=self.__class__.__name__,
                title="Estimated Stage Count",
                description=f"The plan runs as {stage_count} {noun}.",
                severity=Severity.LOW,
                metadata={
                    "positive": True,
                    "category": "stage_count",
                    "stage_count": stage_count,
                    "shuffle_boundary_count": boundary_count,
                },
            )
        )

        return findings
