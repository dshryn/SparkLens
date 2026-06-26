from __future__ import annotations

from models.analysis_finding import AnalysisFinding
from models.enums import OperatorType, Severity
from models.execution_dag import ExecutionDAG

from .base import Rule


class BroadcastJoinRule(Rule):
    """
    Detects join operators and reports deterministic metadata.

    Currently supports:
    - BroadcastHashJoin
    - SortMergeJoin
    - ShuffleHashJoin
    """

    _JOIN_CONFIG = {
        OperatorType.BROADCAST_HASH_JOIN: {
            "title": "Broadcast Hash Join Detected",
            "description": (
                "Spark selected a Broadcast Hash Join for this operator. "
                "This strategy is typically efficient when one side of the "
                "join is sufficiently small to broadcast."
            ),
            "severity": Severity.LOW,
            "strategy": "BroadcastHashJoin",
        },
        OperatorType.SORT_MERGE_JOIN: {
            "title": "Sort Merge Join Detected",
            "description": (
                "Spark selected a Sort Merge Join. "
                "This strategy usually requires both inputs to be shuffled "
                "and sorted before the join."
            ),
            "severity": Severity.MEDIUM,
            "strategy": "SortMergeJoin",
        },
        OperatorType.SHUFFLE_HASH_JOIN: {
            "title": "Shuffle Hash Join Detected",
            "description": (
                "Spark selected a Shuffle Hash Join. "
                "This strategy redistributes data before performing the join "
                "and may introduce shuffle overhead."
            ),
            "severity": Severity.MEDIUM,
            "strategy": "ShuffleHashJoin",
        },
    }

    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:

        findings: list[AnalysisFinding] = []

        for operator in dag.operators.values():

            config = self._JOIN_CONFIG.get(
                operator.operator_type
            )

            if config is None:
                continue

            metadata = {
                "join_strategy": config["strategy"],
                "operator_name": operator.name,
                "operator_type": operator.operator_type.value,
                "depth": str(operator.depth),
                "children": str(len(operator.children)),
            }

            self._copy_metadata(
                operator,
                metadata,
                "Join type",
                "join_type",
            )

            self._copy_metadata(
                operator,
                metadata,
                "Left keys",
                "left_keys",
            )

            self._copy_metadata(
                operator,
                metadata,
                "Right keys",
                "right_keys",
            )

            self._copy_metadata(
                operator,
                metadata,
                "Join condition",
                "join_condition",
            )

            if operator.arguments:
                metadata["arguments"] = ", ".join(
                    operator.arguments
                )

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title=config["title"],
                    description=config["description"],
                    severity=config["severity"],
                    operator_id=operator.operator_id,
                    metadata=metadata,
                )
            )

        return findings

    @staticmethod
    def _copy_metadata(
        operator,
        metadata: dict[str, str],
        source_key: str,
        target_key: str,
    ) -> None:
        """
        Copies parser metadata into analysis metadata if available.
        """

        value = operator.metadata.get(source_key)

        if value:
            metadata[target_key] = value