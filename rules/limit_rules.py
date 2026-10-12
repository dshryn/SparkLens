from __future__ import annotations

import re

from models.analysis_finding import AnalysisFinding
from models.enums import Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class LimitRule(Rule):
    """Detects limit and top-N operators."""

    _INTEGER = re.compile(r"\d+")

    def apply(self, dag: ExecutionDAG) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():
            arguments = " ".join(operator.arguments)
            number = self._first_integer(arguments)

            if number is None:
                continue

            if operator.name == "CollectLimit":
                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Limit Detected",
                        description=(
                            f"Results are capped by a CollectLimit of "
                            f"{number} rows. Only the first rows are "
                            "fetched to the driver."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                    )
                )
            elif operator.name == "TakeOrderedAndProject":
                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Top-N Detected",
                        description=(
                            f"ORDER BY with LIMIT {number} is planned as "
                            f"a TakeOrderedAndProject top-N. Each partition "
                            f"keeps only its top {number} rows, which avoids "
                            "a full global sort and range shuffle."
                        ),
                        severity=Severity.LOW,
                        operator_id=operator.operator_id,
                    )
                )

        return findings

    @classmethod
    def _first_integer(cls, arguments: str) -> int | None:
        match = cls._INTEGER.search(arguments)
        return int(match.group()) if match else None
