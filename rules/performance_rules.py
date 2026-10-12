from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class PerformanceRule(Rule):
    """
    Detects aggregate execution patterns that may represent performance
    bottlenecks.

    Findings describe observed patterns only. RecommendationEngine decides
    whether an actionable recommendation is justified.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        single_partition_ids: list[int] = []
        shuffle_ids: list[int] = []
        sort_count = 0
        aggregation_count = 0

        for operator in dag.operators.values():

            if (
                operator.operator_type
                == OperatorType.EXCHANGE
            ):

                arguments = " ".join(
                    operator.arguments
                ).lower()

                if "singlepartition" in arguments:
                    single_partition_ids.append(
                        operator.operator_id
                    )

                shuffle_ids.append(
                    operator.operator_id
                )

            elif (
                operator.operator_type
                == OperatorType.SORT
            ):

                sort_count += 1

            elif operator.operator_type in (
                OperatorType.HASH_AGGREGATE,
                OperatorType.SORT_AGGREGATE,
            ):

                aggregation_count += 1

        # --------------------------------------------------------------
        # Single partition bottleneck
        # --------------------------------------------------------------

        if single_partition_ids:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Single Partition Bottleneck",
                    description=(
                        "A single-partition exchange was detected. "
                        "This can concentrate work into one task and "
                        "limit parallelism."
                    ),
                    severity=Severity.HIGH,
                    operator_id=single_partition_ids[0],
                    metadata={
                        "operator_ids": single_partition_ids,
                    },
                )
            )

        # --------------------------------------------------------------
        # Multiple shuffles
        # --------------------------------------------------------------

        if len(shuffle_ids) > 1:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Multiple Shuffle Operations",
                    description=(
                        "Multiple shuffle exchanges are present in the "
                        "execution plan."
                    ),
                    severity=Severity.MEDIUM,
                    metadata={
                        "shuffle_operator_ids": shuffle_ids,
                    },
                )
            )

        # --------------------------------------------------------------
        # Multiple sorts
        # --------------------------------------------------------------

        if sort_count > 1:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Multiple Sort Operations",
                    description=(
                        "Multiple sort operations are present in the "
                        "execution plan."
                    ),
                    severity=Severity.MEDIUM,
                    metadata={
                        "sort_count": sort_count,
                    },
                )
            )

        # --------------------------------------------------------------
        # Multi-stage aggregation
        # --------------------------------------------------------------

        if aggregation_count == 2:

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Multi-Stage Aggregation",
                    description=(
                        "Multiple aggregation operators are present, "
                        "indicating a multi-stage aggregation pipeline."
                    ),
                    severity=Severity.LOW,
                    metadata={
                        "positive": True,
                        "category": "multi_stage_aggregation",
                        "aggregation_count": (
                            aggregation_count
                        ),
                    },
                )
            )

        return findings