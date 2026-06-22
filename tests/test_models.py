from models.execution_dag import ExecutionDAG
from models.enums import OperatorType, TransformationType
from models.physical_operator import PhysicalOperator


def main():
    dag = ExecutionDAG()

    scan = PhysicalOperator(
        operator_id=1,
        name="Scan",
        operator_type=OperatorType.FILE_SCAN,
        transformation=TransformationType.NONE,
        depth=0,
    )

    exchange = PhysicalOperator(
        operator_id=2,
        name="Exchange",
        operator_type=OperatorType.EXCHANGE,
        transformation=TransformationType.WIDE,
        depth=1,
    )

    dag.add_operator(scan)
    dag.add_operator(exchange)

    dag.connect(parent_id=2, child_id=1)

    print("\n SparkLens Model Test \n")

    print("\nRoot Nodes:")
    print([op.name for op in dag.root_nodes()])

    print("\nLeaf Nodes:")
    print([op.name for op in dag.leaf_nodes()])

    print("\nTopological Order:")
    print([op.name for op in dag.topological_order()])

    print("\nChildren of Exchange:")
    print([op.name for op in dag.children(2)])

    print("\nParents of Scan:")
    print([op.name for op in dag.parents(1)])

    print("\nAll tests passed.")


if __name__ == "__main__":
    main()