from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class PartitionRule(Rule):
    """
    Detects partitioning strategies used by Spark.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.EXCHANGE:
                continue

            arguments = " ".join(operator.arguments).lower()

            if "singlepartition" in arguments:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Single Partition Detected",
                        description=(
                            "Spark repartitions all data into a single "
                            "partition. This may limit parallelism."
                        ),
                        severity=Severity.HIGH,
                        operator_id=operator.operator_id,
                    )
                )

            elif "hashpartitioning" in arguments:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Hash Partitioning Detected",
                        description=(
                            "Spark redistributes rows using hash "
                            "partitioning across executors."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

            elif "rangepartitioning" in arguments:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Range Partitioning Detected",
                        description=(
                            "Spark redistributes rows using range "
                            "partitioning to preserve ordering."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

        return findings