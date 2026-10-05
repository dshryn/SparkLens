from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator

from .base import Rule


class AggregationRule(Rule):
    """
    Detects aggregation operators and identifies the aggregation phase.

    Phase detection prefers structural DAG evidence so that vanilla Spark
    plans and Photon plans are treated consistently.
    """

    _AGG_TYPES = (
        OperatorType.HASH_AGGREGATE,
        OperatorType.SORT_AGGREGATE,
    )

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type not in self._AGG_TYPES:
                continue

            arguments = " ".join(
                operator.arguments
            ).lower()

            # ----------------------------------------------------------
            # Explicit partial marker remains reliable.
            # ----------------------------------------------------------

            if "partial_" in arguments:

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

                continue

            # ----------------------------------------------------------
            # Structural final/merge detection.
            #
            # Final Aggregate
            #       |
            #    Exchange
            #       |
            # Partial Aggregate
            #
            # Do not require finalmerge_ or merge_ markers.
            # ----------------------------------------------------------

            if self._is_structural_final_aggregation(
                dag,
                operator,
            ):

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Final Aggregation",
                        description=(
                            "Spark performs the final aggregation after "
                            "combining intermediate results across the "
                            "shuffle boundary."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

                continue

            # Photon-specific markers remain optional confirmation.
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

                continue

            if "merge_" in arguments:

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

                continue

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

    def _is_structural_final_aggregation(
        self,
        dag: ExecutionDAG,
        operator: PhysicalOperator,
    ) -> bool:
        """
        Determines whether an aggregation is the final side of a
        two-phase aggregation using DAG structure.

        Expected shape:

            Final Aggregate
                    |
                 Exchange
                    |
            Partial Aggregate
        """

        for exchange in dag.children(
            operator.operator_id
        ):

            if exchange.operator_type != OperatorType.EXCHANGE:
                continue

            upstream = dag.children(
                exchange.operator_id
            )

            for child in upstream:

                if child.operator_type not in self._AGG_TYPES:
                    continue

                arguments = " ".join(
                    child.arguments
                ).lower()

                if "partial_" in arguments:
                    return True

        return False