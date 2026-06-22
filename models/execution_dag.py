from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .base import BaseModel
from .execution_edge import ExecutionEdge
from .physical_operator import PhysicalOperator


@dataclass(slots=True)
class ExecutionDAG(BaseModel):
    """
    Represents a Spark Physical Execution DAG.

    Stores operators and their relationships, independent of any
    visualization library.
    """

    operators: dict[int, PhysicalOperator] = field(default_factory=dict)
    edges: list[ExecutionEdge] = field(default_factory=list)
    parent_map: dict[int, list[int]] = field(default_factory=dict)

    def add_operator(self, operator: PhysicalOperator) -> None:
        """
        Add an operator to the DAG.
        """

        if operator.operator_id in self.operators:
            raise ValueError(
                f"Duplicate operator {operator.operator_id}"
            )

        self.operators[operator.operator_id] = operator
        self.parent_map.setdefault(operator.operator_id, [])

    def connect(self, parent_id: int, child_id: int) -> None:
        """
        Connect two operators with a directed edge.
        """

        if parent_id not in self.operators:
            raise ValueError(
                f"Unknown parent operator {parent_id}"
            )

        if child_id not in self.operators:
            raise ValueError(
                f"Unknown child operator {child_id}"
            )

        edge = ExecutionEdge(
            parent_id=parent_id,
            child_id=child_id,
        )

        if edge not in self.edges:
            self.edges.append(edge)

        parent = self.operators[parent_id]

        if child_id not in parent.children:
            parent.children.append(child_id)

        self.parent_map.setdefault(child_id, [])

        if parent_id not in self.parent_map[child_id]:
            self.parent_map[child_id].append(parent_id)

    def get_operator(
        self,
        operator_id: int,
    ) -> PhysicalOperator:
        return self.operators[operator_id]

    def children(
        self,
        operator_id: int,
    ) -> list[PhysicalOperator]:
        return [
            self.operators[child_id]
            for child_id in self.operators[operator_id].children
        ]

    def parents(
        self,
        operator_id: int,
    ) -> list[PhysicalOperator]:
        return [
            self.operators[parent_id]
            for parent_id in self.parent_map.get(operator_id, [])
        ]

    def root_nodes(self) -> list[PhysicalOperator]:
        return [
            operator
            for operator in self.operators.values()
            if len(self.parent_map[operator.operator_id]) == 0
        ]

    def leaf_nodes(self) -> list[PhysicalOperator]:
        return [
            operator
            for operator in self.operators.values()
            if len(operator.children) == 0
        ]

    def topological_order(self) -> list[PhysicalOperator]:
        """
        Return operators in topological order.

        Raises
        ------
        ValueError
            If the graph contains a cycle.
        """

        indegree = {
            operator_id: len(parents)
            for operator_id, parents in self.parent_map.items()
        }

        queue = deque(
            operator_id
            for operator_id, degree in indegree.items()
            if degree == 0
        )

        ordering: list[PhysicalOperator] = []

        while queue:
            node = queue.popleft()
            ordering.append(self.operators[node])

            for child in self.operators[node].children:
                indegree[child] -= 1

                if indegree[child] == 0:
                    queue.append(child)

        if len(ordering) != len(self.operators):
            raise ValueError(
                "Cycle detected in execution DAG."
            )

        return ordering