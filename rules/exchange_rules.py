from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class ExchangeRule(Rule):
    """
    Detects data exchange operations in the execution DAG.

    Like ShuffleRule, this rule records the raw observation only. It does
    not decide whether the exchange is required or unnecessary --
    ExecutionQualityRule supplies that evidence, and RecommendationEngine
    uses it to suppress recommendations for exchanges it has marked
    "required": True.
    """

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.EXCHANGE:
                continue

            name = operator.name.lower()

            if "broadcastexchange" in name:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Broadcast Exchange",
                        description=(
                            "Spark broadcasts a small dataset to all "
                            "executors to avoid a shuffle during joins."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                    )
                )

            elif "shuffleexchangesink" in name:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Shuffle Write",
                        description=(
                            "Spark writes shuffle data for downstream "
                            "stages. Whether this exchange is required is "
                            "determined by ExecutionQualityRule's evidence "
                            "for this operator."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

            elif "shuffleexchangesource" in name:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Shuffle Read",
                        description=(
                            "Spark reads data produced by a previous "
                            "shuffle stage. Whether this exchange is "
                            "required is determined by "
                            "ExecutionQualityRule's evidence for this "
                            "operator."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

            else:

                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Exchange Operator",
                        description=(
                            "Spark exchanges data between execution "
                            "stages. Whether this exchange is required is "
                            "determined by ExecutionQualityRule's evidence "
                            "for this operator."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )

        return findings