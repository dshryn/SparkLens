from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class AggregationRule(Rule):
    """
    Detects aggregation operators and identifies the aggregation phase.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type not in (
                OperatorType.HASH_AGGREGATE,
                OperatorType.SORT_AGGREGATE,
            ):
                continue

            arguments = " ".join(operator.arguments).lower()

            if "finalmerge_" in arguments:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Final Aggregation",
                        description=(
                            "Spark performs the final aggregation after "
                            "combining intermediate results."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

            elif "merge_" in arguments:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Merge Aggregation",
                        description=(
                            "Spark merges intermediate aggregation "
                            "results received from upstream partitions."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

            elif "partial_" in arguments:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Partial Aggregation",
                        description=(
                            "Spark performs a local aggregation before "
                            "redistributing data."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                    )
                )

            else:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Aggregation",
                        description=(
                            "Spark performs an aggregation operation."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                    )
                )

        return findings