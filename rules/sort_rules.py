from __future__ import annotations

import re

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class SortRule(Rule):
    """
    Detects sort operations in the execution DAG.
    """

    _MERGE_CONSUMERS = (
        OperatorType.SORT_MERGE_JOIN,
        OperatorType.SORT_AGGREGATE,
    )

    # Spark prints "[col ASC NULLS FIRST], false, 0" for a per-partition sort.
    _LOCAL_SORT = re.compile(r"\]\s*,\s*false\b", re.IGNORECASE)

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        has_exchange = any(
            operator.operator_type == OperatorType.EXCHANGE
            for operator in dag.operators.values()
        )

        for operator in dag.operators.values():

            if operator.operator_type != OperatorType.SORT:
                continue

            arguments = " ".join(operator.arguments)

            feeds_merge = any(
                parent.operator_type in self._MERGE_CONSUMERS
                for parent in dag.parents(operator.operator_id)
            )

            is_local = bool(self._LOCAL_SORT.search(arguments))

            if is_local and not feeds_merge and not has_exchange:
                description = (
                    "The sort is local to each partition and the plan "
                    "contains no shuffle."
                )

            else:
                description = (
                    "Spark sorts the dataset before downstream processing."
                )

                if not feeds_merge and not is_local:

                    if "ASC" in arguments:
                        description += " Sort order: Ascending."

                    elif "DESC" in arguments:
                        description += " Sort order: Descending."

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title="Sort Operation Detected",
                    description=description,
                    severity=Severity.MEDIUM,
                    operator_id=operator.operator_id,
                )
            )

        return findings
