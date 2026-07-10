from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class PerformanceRule(Rule):
    """
    Detects common performance characteristics of a Spark execution plan.

    NOTE: "Multi-Stage Aggregation" is an EXPECTED-COST / POSITIVE
    observation, not an actionable optimization opportunity -- two or
    more aggregation operators is exactly what Spark's standard
    two-phase (partial + final) aggregation strategy looks like. It is
    marked with metadata "positive": True so RecommendationEngine never
    turns it into a generic "review the plan" recommendation. All other
    findings in this rule (single-partition bottleneck, multiple
    shuffles, multiple sorts) remain unmarked because they represent
    real, evidence-backed concerns.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        single_partition = 0
        shuffle_count = 0
        sort_count = 0
        aggregation_count = 0

        for operator in dag.operators.values():

            if operator.operator_type == OperatorType.EXCHANGE:

                arguments = " ".join(operator.arguments).lower()

                if "singlepartition" in arguments:
                    single_partition += 1

                if "shuffle" in operator.name.lower():
                    shuffle_count += 1

            elif operator.operator_type == OperatorType.SORT:
                sort_count += 1

            elif operator.operator_type in (
                OperatorType.HASH_AGGREGATE,
                OperatorType.SORT_AGGREGATE,
            ):
                aggregation_count += 1

        if single_partition:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Single Partition Bottleneck",
                    description=(
                        "The execution plan contains a "
                        "SinglePartition exchange, which may reduce "
                        "parallelism by processing data in a single "
                        "partition."
                    ),
                    severity=Severity.HIGH,
                )
            )

        if shuffle_count >= 2:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Multiple Shuffle Operations",
                    description=(
                        f"The plan contains {shuffle_count} shuffle "
                        "exchange operators. Multiple shuffles may "
                        "increase network I/O and execution time."
                    ),
                    severity=Severity.MEDIUM,
                )
            )

        if sort_count >= 2:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Multiple Sort Operations",
                    description=(
                        f"The plan contains {sort_count} sort "
                        "operators. Repeated sorting can increase "
                        "execution time."
                    ),
                    severity=Severity.MEDIUM,
                )
            )

        if aggregation_count >= 2:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Multi-Stage Aggregation",
                    description=(
                        "Spark performs aggregation in multiple stages, "
                        "which is expected for distributed execution "
                        "(e.g. a partial map-side aggregation followed "
                        "by a final merge aggregation)."
                    ),
                    severity=Severity.LOW,
                    metadata={
                        "positive": True,
                        "category": "multi_stage_aggregation",
                    },
                )
            )

        return findings