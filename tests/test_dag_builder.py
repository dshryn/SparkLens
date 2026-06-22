from analyzer.dag_builder import DAGBuilder
from models.enums import OperatorType, TransformationType
from models.parsed_plan import ParsedPlan
from models.physical_operator import PhysicalOperator

import pytest



def make_operator(operator_id: int) -> PhysicalOperator:
    return PhysicalOperator(
        operator_id=operator_id,
        name=f"Operator{operator_id}",
        operator_type=OperatorType.UNKNOWN,
        transformation=TransformationType.NONE,
    )


def test_build_empty_dag():
    builder = DAGBuilder()

    dag = builder.build(ParsedPlan())

    assert len(dag.operators) == 0
    assert len(dag.edges) == 0


def test_build_single_operator():
    builder = DAGBuilder()

    operator = make_operator(1)

    dag = builder.build(
        ParsedPlan(
            operators={
                1: operator,
            }
        )
    )

    assert len(dag.operators) == 1
    assert dag.root_nodes() == [operator]
    assert dag.leaf_nodes() == [operator]


def test_build_linear_dag():
    builder = DAGBuilder()

    operators = {
        1: make_operator(1),
        2: make_operator(2),
        3: make_operator(3),
    }

    dag = builder.build(
        ParsedPlan(
            operators=operators,
            edges=[
                (1, 2),
                (2, 3),
            ],
        )
    )

    assert operators[2].operator_id in operators[1].children
    assert operators[3].operator_id in operators[2].children

    assert dag.parents(2) == [operators[1]]
    assert dag.parents(3) == [operators[2]]

    assert dag.root_nodes() == [operators[1]]
    assert dag.leaf_nodes() == [operators[3]]


def test_build_branching_dag():
    builder = DAGBuilder()

    operators = {
        1: make_operator(1),
        2: make_operator(2),
        3: make_operator(3),
    }

    dag = builder.build(
        ParsedPlan(
            operators=operators,
            edges=[
                (1, 2),
                (1, 3),
            ],
        )
    )

    assert set(operators[1].children) == {2, 3}

    assert dag.parents(2) == [operators[1]]
    assert dag.parents(3) == [operators[1]]

    assert dag.root_nodes() == [operators[1]]

    leaves = dag.leaf_nodes()
    assert set(op.operator_id for op in leaves) == {2, 3}


def test_invalid_parent():
    builder = DAGBuilder()

    operators = {
        1: make_operator(1),
    }

    plan = ParsedPlan(
        operators=operators,
        edges=[
            (2, 1),
        ],
    )

    try:
        builder.build(plan)
        assert False
    except ValueError:
        pass


def test_invalid_child():
    builder = DAGBuilder()

    operators = {
        1: make_operator(1),
    }

    plan = ParsedPlan(
        operators=operators,
        edges=[
            (1, 2),
        ],
    )


    with pytest.raises(ValueError):
        builder.build(plan)