import matplotlib

matplotlib.use("Agg")

import networkx as nx  # noqa: E402

from models.analysis_report import AnalysisReport  # noqa: E402
from models.enums import OperatorType, TransformationType  # noqa: E402
from models.execution_dag import ExecutionDAG  # noqa: E402
from models.physical_operator import PhysicalOperator  # noqa: E402
from visualization.dag import DAGVisualizer  # noqa: E402
from visualization.networkx_renderer import GraphRenderer  # noqa: E402


def test_visualizer_import():
    assert DAGVisualizer is not None


def test_layered_layout_draws_every_edge_downwards():
    # A join: the root (5) has one child (4) that reads two branches.
    dag = nx.DiGraph([(5, 4), (4, 3), (4, 1), (3, 2)])

    pos, _ = GraphRenderer._layered_layout(dag)

    for parent, child in dag.edges:
        assert pos[parent][1] > pos[child][1]

    # The two branches under the join sit side by side, not on top of each other.
    assert pos[3][1] == pos[1][1]
    assert pos[3][0] != pos[1][0]


def test_layered_layout_grows_the_figure_for_wide_plans():
    narrow = nx.DiGraph([(2, 1)])
    wide = nx.DiGraph([(0, child) for child in range(1, 9)])

    _, narrow_size = GraphRenderer._layered_layout(narrow)
    _, wide_size = GraphRenderer._layered_layout(wide)

    assert wide_size[0] > narrow_size[0]


def test_layered_layout_wraps_graphs_without_edges():
    dag = nx.DiGraph()
    dag.add_nodes_from(range(1, 33))

    pos, size = GraphRenderer._layered_layout(dag)

    assert len({y for _, y in pos.values()}) > 1   # several rows, not one
    assert size[0] < 20


def test_save_writes_png(tmp_path):
    dag = ExecutionDAG()

    for operator_id, name, operator_type in (
        (1, "Scan", OperatorType.FILE_SCAN),
        (2, "Exchange", OperatorType.EXCHANGE),
        (3, "HashAggregate", OperatorType.HASH_AGGREGATE),
    ):
        dag.add_operator(
            PhysicalOperator(
                operator_id=operator_id,
                name=name,
                operator_type=operator_type,
                transformation=TransformationType.NONE,
            )
        )

    dag.connect(3, 2)
    dag.connect(2, 1)

    path = tmp_path / "dag.png"

    DAGVisualizer().save(dag, AnalysisReport(), str(path))

    assert path.exists()
    assert path.stat().st_size > 0
