from models.analysis_finding import AnalysisFinding
from models.analysis_report import AnalysisReport
from models.enums import OperatorType, Severity, TransformationType
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator
from visualization.graph_builder import GraphBuilder


def build_sample_dag() -> ExecutionDAG:
    dag = ExecutionDAG()

    scan = PhysicalOperator(
        operator_id=1,
        name="Scan",
        operator_type=OperatorType.FILE_SCAN,
        transformation=TransformationType.NONE,
    )

    project = PhysicalOperator(
        operator_id=2,
        name="Project",
        operator_type=OperatorType.PROJECT,
        transformation=TransformationType.NARROW,
    )

    exchange = PhysicalOperator(
        operator_id=3,
        name="Exchange",
        operator_type=OperatorType.EXCHANGE,
        transformation=TransformationType.WIDE,
    )

    dag.add_operator(scan)
    dag.add_operator(project)
    dag.add_operator(exchange)

    dag.connect(1, 2)
    dag.connect(2, 3)

    return dag


def test_build_graph():
    dag = build_sample_dag()

    report = AnalysisReport()

    report.add_finding(
        AnalysisFinding(
            rule="ShuffleRule",
            title="Shuffle Detected",
            description="Shuffle occurs here.",
            severity=Severity.HIGH,
            operator_id=3,
        )
    )

    graph = GraphBuilder().build(dag, report)

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2

    exchange = next(node for node in graph.nodes if node.id == 3)

    assert exchange.highlighted
    assert exchange.severity == Severity.HIGH

    project = next(node for node in graph.nodes if node.id == 2)

    assert not project.highlighted
    assert project.severity is None


def test_highest_severity_is_selected():
    dag = build_sample_dag()

    report = AnalysisReport()

    report.add_finding(
        AnalysisFinding(
            rule="Rule1",
            title="Low Severity",
            description="",
            severity=Severity.LOW,
            operator_id=3,
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="Rule2",
            title="Critical Severity",
            description="",
            severity=Severity.CRITICAL,
            operator_id=3,
        )
    )

    graph = GraphBuilder().build(dag, report)

    exchange = next(node for node in graph.nodes if node.id == 3)

    assert exchange.highlighted
    assert exchange.severity == Severity.CRITICAL