from __future__ import annotations

from models.execution_dag import ExecutionDAG
from models.parsed_plan import ParsedPlan


class DAGBuilder:
    """
    Builds an ExecutionDAG from a parsed execution plan.

    The builder is responsible for graph construction AND for assigning
    each operator's depth, since depth is a structural property of the
    graph (longest path from a root) and DAGBuilder is the one place that
    already has both the complete operator set and the fully-connected
    parent/child structure available in one pass.
    """

    def build(
        self,
        parsed_plan: ParsedPlan,
    ) -> ExecutionDAG:
        """
        Construct an ExecutionDAG from a ParsedPlan.
        """

        dag = ExecutionDAG()

        for operator in parsed_plan.operators.values():
            dag.add_operator(operator)

        for parent_id, child_id in parsed_plan.edges:
            dag.connect(parent_id, child_id)

        self._assign_depths(dag)

        return dag

    def _assign_depths(self, dag: ExecutionDAG) -> None:
        """
        Assigns operator.depth as 1 + (longest chain of ancestors above it),
        so a root operator (no parents) has depth 1, and each subsequent
        operator's depth is 1 + the maximum depth of its parents.

        Processing operators in topological order (via dag.topological_order())
        guarantees every parent's depth has already been finalized before
        any of its children are visited, so a single forward pass is
        sufficient -- this is not a general longest-path problem requiring
        repeated relaxation, because the DAG has no cycles (topological_order
        itself raises ValueError if one exists).
        """

        for operator in dag.topological_order():
            parent_ids = dag.parent_map.get(operator.operator_id, [])

            if not parent_ids:
                operator.depth = 1
            else:
                operator.depth = 1 + max(
                    dag.operators[parent_id].depth
                    for parent_id in parent_ids
                )