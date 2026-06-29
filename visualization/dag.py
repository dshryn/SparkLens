"""Public API for execution DAG visualization."""

from __future__ import annotations

from visualization.base_renderer import BaseRenderer
from visualization.graph_builder import GraphBuilder
from visualization.models import GraphModel
from visualization.networkx_renderer import GraphRenderer

from models.analysis_report import AnalysisReport
from models.execution_dag import ExecutionDAG


class DAGVisualizer:
    """
    Public entry point for execution DAG visualization.
    """

    def __init__(
        self,
        renderer: BaseRenderer | None = None,
    ) -> None:
        self._builder = GraphBuilder()
        self._renderer = renderer if renderer is not None else GraphRenderer()

    @property
    def renderer(self) -> BaseRenderer:
        return self._renderer

    def build(
        self,
        dag: ExecutionDAG,
        report: AnalysisReport,
    ) -> GraphModel:
        """
        Build a GraphModel from the execution DAG.
        """

        return self._builder.build(
            dag,
            report,
        )

    def visualize(
        self,
        dag: ExecutionDAG,
        report: AnalysisReport,
    ) -> None:
        """
        Build and render the graph.
        """

        graph = self.build(
            dag,
            report,
        )

        self._renderer.render(
            graph,
        )

    def save(
        self,
        dag: ExecutionDAG,
        report: AnalysisReport,
        path: str,
    ) -> None:
        """
        Build and save the graph.
        """

        graph = self.build(
            dag,
            report,
        )

        self._renderer.save(
            graph,
            path,
        )

    def render_graph(
        self,
        graph: GraphModel,
    ) -> None:
        """
        Render an existing GraphModel.
        """

        self._renderer.render(
            graph,
        )

    def save_graph(
        self,
        graph: GraphModel,
        path: str,
    ) -> None:
        """
        Save an existing GraphModel.
        """

        self._renderer.save(
            graph,
            path,
        )
