from __future__ import annotations

import re

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

            if operator.name == "CartesianProduct":
                findings.append(
                    AnalysisFinding(
                        rule=self.__class__.__name__,
                        title="Cartesian Product Detected",
                        description=(
                            "A cartesian product should be avoided unless "
                            "the cross join is truly intended."
                        ),
                        severity=Severity.MEDIUM,
                        operator_id=operator.operator_id,
                    )
                )
                continue

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

            description = config["description"]
            keys = self._join_keys(operator)

            join_type = operator.metadata.get("Join type", "")
            if (
                operator.operator_type == OperatorType.SORT_MERGE_JOIN
                and "fullouter" in join_type.lower().replace(" ", "")
            ):
                description += " A full outer join cannot be broadcast."

            if keys and config["strategy"] in (
                "SortMergeJoin",
                "ShuffleHashJoin",
            ) and self._both_sides_have_exchange(dag, operator):
                if config["strategy"] == "SortMergeJoin":
                    description += (
                        " Both inputs are hash-partitioned and sorted on "
                        f"{keys}, and these shuffles are required by the join."
                    )
                else:
                    description += (
                        " Both sides are hash-partitioned on "
                        f"{keys} and joined without a sort step."
                    )

            findings.append(
                AnalysisFinding(
                    rule=self.__class__.__name__,
                    title=config["title"],
                    description=description,
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

    @staticmethod
    def _join_keys(operator) -> str | None:
        raw_keys = operator.metadata.get("Left keys") or operator.metadata.get(
            "left_keys"
        )

        if not raw_keys:
            return None

        keys: list[str] = []

        for raw_key in str(raw_keys).strip("[]").split(","):
            key = re.sub(r"#\d+L?$", "", raw_key.strip()).strip("[] ")

            if key and key not in keys:
                keys.append(key)

        return " and ".join(keys) or None

    @classmethod
    def _both_sides_have_exchange(
        cls,
        dag: ExecutionDAG,
        join,
    ) -> bool:
        children = dag.children(join.operator_id)

        return len(children) >= 2 and all(
            cls._has_exchange_below(dag, child.operator_id)
            for child in children[:2]
        )

    @classmethod
    def _has_exchange_below(
        cls,
        dag: ExecutionDAG,
        operator_id: int,
    ) -> bool:
        visited: set[int] = set()
        frontier = list(dag.children(operator_id))

        while frontier:
            current = frontier.pop()

            if current.operator_id in visited:
                continue

            visited.add(current.operator_id)

            if current.operator_type == OperatorType.EXCHANGE:
                return True

            name = current.name.lower()
            if current.operator_type == OperatorType.SORT or (
                current.operator_type == OperatorType.UNKNOWN
                and (
                    "shuffleread" in name
                    or "shufflequerystage" in name
                )
            ):
                frontier.extend(
                    dag.children(current.operator_id)
                )

        return False