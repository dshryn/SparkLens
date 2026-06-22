"""Public API for execution DAG visualization."""

from models.analysis_report import AnalysisReport
from models.execution_dag import ExecutionDAG
from visualization.graph_builder import GraphBuilder
from visualization.renderer import GraphRenderer


class DAGVisualizer:
    """Visualizes Spark execution DAGs."""

    def __init__(self):
        self._builder = GraphBuilder()
        self._renderer = GraphRenderer()

    def visualize(
        self,
        dag: ExecutionDAG,
        report: AnalysisReport,
    ) -> None:
        """
        Builds and renders an execution graph.
        """

        graph = self._builder.build(dag, report)
        self._renderer.render(graph)