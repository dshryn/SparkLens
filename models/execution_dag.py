from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .base import BaseModel
from .physical_operator import PhysicalOperator


@dataclass(slots=True)
class ExecutionDAG(BaseModel):
    """
    Represents a Spark Physical Execution DAG.

    Stores operators and their relationships, independent of any
    visualization library.
    """

    operators: dict[int, PhysicalOperator] = field(default_factory=dict)
    parent_map: dict[int, list[int]] = field(default_factory=dict)

    def add_operator(self, operator: PhysicalOperator) -> None:
        self.operators[operator.operator_id] = operator
        self.parent_map.setdefault(operator.operator_id, [])

    def connect(self, parent_id: int, child_id: int) -> None:
        if parent_id not in self.operators:
            raise ValueError(f"Unknown parent operator {parent_id}")

        if child_id not in self.operators:
            raise ValueError(f"Unknown child operator {child_id}")

        parent = self.operators[parent_id]

        if child_id not in parent.children:
            parent.children.append(child_id)

        self.parent_map.setdefault(child_id, [])

        if parent_id not in self.parent_map[child_id]:
            self.parent_map[child_id].append(parent_id)

    def get_operator(self, operator_id: int) -> PhysicalOperator:
        return self.operators[operator_id]

    def children(self, operator_id: int) -> list[PhysicalOperator]:
        return [
            self.operators[c]
            for c in self.operators[operator_id].children
        ]

    def parents(self, operator_id: int) -> list[PhysicalOperator]:
        return [
            self.operators[p]
            for p in self.parent_map.get(operator_id, [])
        ]

    def root_nodes(self) -> list[PhysicalOperator]:
        return [
            op
            for op in self.operators.values()
            if len(self.parent_map[op.operator_id]) == 0
        ]

    def leaf_nodes(self) -> list[PhysicalOperator]:
        return [
            op
            for op in self.operators.values()
            if len(op.children) == 0
        ]

    def topological_order(self) -> list[PhysicalOperator]:
        indegree = {
            node_id: len(parents)
            for node_id, parents in self.parent_map.items()
        }

        queue = deque(
            node_id
            for node_id, degree in indegree.items()
            if degree == 0
        )

        ordering = []

        while queue:
            node = queue.popleft()
            ordering.append(self.operators[node])

            for child in self.operators[node].children:
                indegree[child] -= 1

                if indegree[child] == 0:
                    queue.append(child)

        return ordering