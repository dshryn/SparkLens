from models.enums import (
    OperatorType,
    Severity,
    TransformationType,
)
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator
from rules.engine import RuleEngine
from rules.join_rules import BroadcastJoinRule


def make_operator(
    operator_id: int,
    name: str,
    operator_type: OperatorType = OperatorType.UNKNOWN,
) -> PhysicalOperator:return PhysicalOperator(
    operator_id=operator_id,
    name=name,
    operator_type=operator_type,
    transformation=TransformationType.NONE,
)


def test_broadcast_join_detected():

    dag = ExecutionDAG()

    dag.add_operator(
    make_operator(
        1,
        "PhotonBroadcastHashJoin",
        OperatorType.BROADCAST_HASH_JOIN,
    )
)

    report = RuleEngine(
        [BroadcastJoinRule()]
    ).run(dag)

    assert report.has_findings()

    assert len(report.findings) == 1

    finding = report.findings[0]

    assert finding.operator_id == 1
    assert finding.severity == Severity.LOW
    assert finding.rule == "BroadcastJoinRule"


def test_no_broadcast_join():

    dag = ExecutionDAG()

    dag.add_operator(
        make_operator(
            1,
            "PhotonProject",
        )
    )

    report = RuleEngine(
        [BroadcastJoinRule()]
    ).run(dag)

    assert not report.has_findings()