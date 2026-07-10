from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import Severity, TransformationType
from models.execution_dag import ExecutionDAG

from .base import Rule


class StageRule(Rule):
    """
    Detects Spark stage boundaries.

    IMPORTANT: This rule's stage count MUST use the exact same
    definition as SparkAnalyzer._compute_statistics's canonical formula
    (one initial stage, plus one additional stage for every WIDE
    transformation) so that ExecutionStatistics.stage_count and this
    rule's "Estimated Stage Count" finding can never disagree. Do not
    recompute stage boundaries using an independent heuristic (e.g.
    matching on operator name substrings like "shuffleexchangesink") --
    that was the previous source of inconsistent stage counts between
    statistics and findings.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        stage_count = 1

        for operator in dag.operators.values():

            if operator.transformation != TransformationType.WIDE:
                continue

            stage_count += 1

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Stage Boundary Detected",
                    description=(
                        "This operator is a wide (shuffle-boundary) "
                        "transformation and introduces a new Spark "
                        "stage."
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
                metadata={
                    "positive": True,
                    "category": "stage_count",
                    "stage_count": stage_count,
                },
            )
        )

        return findings