from pathlib import Path

from analyzer.dag_builder import DAGBuilder
from analyzer.parser import PlanParser
from models.analysis_report import AnalysisReport
from visualization.dag import DAGVisualizer
from visualization.graph_builder import GraphBuilder
from visualization.interactive_renderer import InteractiveRenderer


CUSTOMER_PLAN = Path("test_plans/customer_analytics.txt").read_text(
    encoding="utf-8"
)


def assert_graph_edges(plan: str, operator_count: int, edge_count: int):
    parsed = PlanParser().parse(plan)
    assert len(parsed.operators) == operator_count
    assert len(parsed.edges) == edge_count
    assert all(
        parent in parsed.operators and child in parsed.operators
        for parent, child in parsed.edges
    )

    dag = DAGBuilder().build(parsed)
    dag_edges = [(edge.parent_id, edge.child_id) for edge in dag.edges]
    assert dag_edges == parsed.edges

    graph = GraphBuilder().build(dag, AnalysisReport())
    graph_edges = [(edge.source, edge.target) for edge in graph.edges]
    assert graph_edges == dag_edges
    assert graph_edges

    return parsed, dag, graph


def test_numbered_sample_plan_preserves_existing_edges():
    plan = Path("sample_plans/aggregation.txt").read_text(encoding="utf-8")
    parsed, _, _ = assert_graph_edges(plan, 7, 6)

    assert parsed.edges == [(7, 6), (6, 5), (5, 4), (4, 3), (3, 2), (2, 1)]


def test_unnumbered_customer_plan_uses_tree_order_and_skips_adaptive_wrapper():
    parsed, _, _ = assert_graph_edges(CUSTOMER_PLAN, 25, 24)

    assert "AdaptiveSparkPlan" not in {operator.name for operator in parsed.operators.values()}
    assert (5, 6) in parsed.edges
    assert (5, 22) in parsed.edges
    assert (6, 7) in parsed.edges
    assert (6, 18) in parsed.edges
    assert (13, 14) in parsed.edges
    assert (13, 15) in parsed.edges


def test_tree_only_plan_numbers_non_wrapper_nodes():
    plan = """\
AdaptiveSparkPlan isFinalPlan=false
+- Project
   +- Filter
      +- Scan parquet t
"""
    parsed, _, _ = assert_graph_edges(plan, 3, 2)

    assert parsed.edges == [(1, 2), (2, 3)]


def test_detail_only_ids_do_not_override_tree_order():
    """Tree structure is authoritative when detail blocks contain the IDs."""
    plan = """\
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project
   +- Scan

(1) Scan
Output [1]: [id]

(2) Project
Output [1]: [id]
"""
    parsed, _, _ = assert_graph_edges(plan, 2, 1)

    assert parsed.edges == [(1, 2)]
    assert [operator.name for operator in parsed.operators.values()] == [
        "Project",
        "Scan",
    ]


def test_repeated_operator_names_follow_tree_depth():
    plan = """\
AdaptiveSparkPlan
+- Exchange
   +- FileScan
      +- Exchange
         +- FileScan
"""
    parsed, _, _ = assert_graph_edges(plan, 4, 3)

    assert parsed.edges == [(1, 2), (2, 3), (3, 4)]


def test_photon_and_columnar_operator_names_have_edges():
    plan = """\
AdaptiveSparkPlan
+- ColumnarToRow
   +- PhotonProject
      +- PhotonBroadcastHashJoin
         :- PhotonRange
         +- PhotonRange
"""
    parsed, _, _ = assert_graph_edges(plan, 5, 4)

    assert parsed.edges == [(1, 2), (2, 3), (3, 4), (3, 5)]


def test_stage_wrappers_are_excluded_and_edges_skip_them():
    plan = """\
AdaptiveSparkPlan
+- ResultStage
   +- Project
      +- ShuffleMapStage
         +- BroadcastQueryStage
            +- WholeStageCodegen
               +- Scan
"""
    parsed, _, _ = assert_graph_edges(plan, 2, 1)

    assert {operator.name for operator in parsed.operators.values()} == {
        "Project",
        "Scan",
    }
    assert parsed.edges == [(1, 2)]


def test_colon_connectors_keep_nested_filter_under_exchange():
    plan = """\
AdaptiveSparkPlan
+- SortMergeJoin
   :- Exchange
   :  +- Filter
   :     +- Project
   :        +- FileScan
   +- Exchange
      +- FileScan
"""
    parsed, _, _ = assert_graph_edges(plan, 7, 6)

    assert parsed.edges[:4] == [(1, 2), (2, 3), (3, 4), (4, 5)]
    assert (1, 6) in parsed.edges


def test_png_and_interactive_renderers_receive_graph_edges(tmp_path):
    parsed, dag, graph = assert_graph_edges(CUSTOMER_PLAN, 25, 24)
    report = AnalysisReport()
    png_path = tmp_path / "dag.png"

    DAGVisualizer().save(dag, report, str(png_path))

    assert png_path.exists()
    network = InteractiveRenderer()._build_network(graph)
    assert len(network.edges) == len(graph.edges)
    assert parsed.edges
