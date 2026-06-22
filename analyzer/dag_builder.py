from __future__ import annotations

from models.execution_dag import ExecutionDAG
from models.parsed_plan import ParsedPlan


class DAGBuilder:
    """
    Builds an ExecutionDAG from a parsed execution plan.

    The builder is responsible only for graph construction.
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

        return dag