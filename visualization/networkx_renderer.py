"""Renders visualization graphs."""

import math

import matplotlib.pyplot as plt
import networkx as nx

from matplotlib.lines import Line2D
from networkx.drawing.nx_pydot import graphviz_layout

from models.enums import Severity

from visualization.base_renderer import BaseRenderer
from visualization.models import GraphModel
from visualization.styles import GraphStyle


class GraphRenderer(BaseRenderer):
    """Renders a GraphModel using NetworkX."""

    def _draw(
        self,
        graph: GraphModel,
    ) -> None:

        dag = nx.DiGraph()

        for node in graph.nodes:
            dag.add_node(
                node.id,
                label=f"{node.label[:12]}\n#{node.id}",
                color=GraphStyle.node_color(node.severity),
                size=GraphStyle.node_size(node.highlighted),
            )

        for edge in graph.edges:
            dag.add_edge(
                edge.source,
                edge.target,
            )

        pos, figsize = self._layout(dag)

        colors = [dag.nodes[node]["color"] for node in dag.nodes]

        sizes = [dag.nodes[node]["size"] for node in dag.nodes]

        labels = {node: dag.nodes[node]["label"] for node in dag.nodes}

        plt.figure(figsize=figsize)

        nx.draw_networkx_nodes(
            dag,
            pos,
            node_color=colors,
            node_size=sizes,
        )

        # Passing the node sizes makes each arrow stop at the edge of its
        # target node instead of ending hidden underneath it.
        nx.draw_networkx_edges(
            dag,
            pos,
            node_size=sizes,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=20,
            width=GraphStyle.EDGE_WIDTH,
            edge_color=GraphStyle.EDGE_COLOR,
        )

        nx.draw_networkx_labels(
            dag,
            pos,
            labels,
            font_size=7,
            font_weight="bold",
        )

        plt.title(
            f"SparkLens Execution DAG\n"
            f"Nodes: {len(graph.nodes)} | "
            f"Edges: {len(graph.edges)}",
            fontsize=16,
            pad=20,
        )

        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Low",
                markerfacecolor=GraphStyle.SEVERITY_COLORS[Severity.LOW],
                markersize=10,
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Medium",
                markerfacecolor=GraphStyle.SEVERITY_COLORS[Severity.MEDIUM],
                markersize=10,
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="High",
                markerfacecolor=GraphStyle.SEVERITY_COLORS[Severity.HIGH],
                markersize=10,
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Critical",
                markerfacecolor=GraphStyle.SEVERITY_COLORS[Severity.CRITICAL],
                markersize=10,
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="No Findings",
                markerfacecolor=GraphStyle.NODE_COLOR,
                markersize=10,
            ),
        ]

        plt.legend(
            handles=legend_elements,
            loc="upper left",
            frameon=True,
        )

        plt.axis("off")
        plt.tight_layout()

    def _layout(
        self,
        dag: nx.DiGraph,
    ) -> tuple[dict, tuple[float, float]]:
        """
        Node positions and figure size.

        Graphviz's "dot" layout is used when Graphviz is installed. Without
        it, the plan is drawn top-down by the layered layout below, which
        needs no extra software.
        """

        try:
            return (
                graphviz_layout(
                    dag,
                    prog="dot",
                ),
                (16, 9),
            )
        except Exception:
            pass

        try:
            return self._layered_layout(dag)
        except nx.NetworkXUnfeasible:
            return (
                nx.spring_layout(
                    dag,
                    seed=42,
                ),
                (16, 9),
            )

    @staticmethod
    def _layered_layout(
        dag: nx.DiGraph,
    ) -> tuple[dict, tuple[float, float]]:
        """
        One row per DAG level with the root at the top, so every edge
        points downwards. Each node is placed near the average position of
        its parents, which keeps branches apart and avoids crossing edges.
        """

        if dag.number_of_edges() == 0 and dag.number_of_nodes() > 0:
            # Operators without any edges (e.g. a plan tree without the
            # "(N)" operator ids) are wrapped into a grid, not one long row.
            columns = math.ceil(math.sqrt(dag.number_of_nodes()))
            rows = math.ceil(dag.number_of_nodes() / columns)

            pos = {
                node: (index % columns, -(index // columns))
                for index, node in enumerate(sorted(dag.nodes))
            }

            return pos, (max(10.0, 1.8 * columns + 4), max(7.0, 1.3 * rows + 2))

        levels = list(nx.topological_generations(dag))

        pos: dict = {}

        def parent_position(node) -> float:
            parents = [pos[parent][0] for parent in dag.predecessors(node)]
            return sum(parents) / len(parents) if parents else 0.0

        for depth, level in enumerate(levels):

            ordered = sorted(
                level,
                key=lambda node: (parent_position(node), node),
            )

            offset = (len(ordered) - 1) / 2

            for index, node in enumerate(ordered):
                pos[node] = (index - offset, -depth)

        widest = max((len(level) for level in levels), default=1)

        figsize = (
            max(10.0, 1.8 * widest + 4),
            max(7.0, 1.3 * len(levels) + 2),
        )

        return pos, figsize

    def render(
        self,
        graph: GraphModel,
    ) -> None:

        self._draw(graph)

        plt.show()

    def save(
        self,
        graph: GraphModel,
        path: str,
    ) -> None:

        self._draw(graph)

        plt.savefig(
            path,
            bbox_inches="tight",
        )

        plt.close()
