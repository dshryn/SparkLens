"""Renders visualization graphs."""

import matplotlib.pyplot as plt
import networkx as nx

from matplotlib.lines import Line2D
from networkx.drawing.nx_pydot import graphviz_layout

from models.enums import Severity

from visualization.models import GraphModel
from visualization.styles import GraphStyle


class GraphRenderer:
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
                color=GraphStyle.node_color(
                    node.severity
                ),
                size=GraphStyle.node_size(
                    node.highlighted
                ),
            )

        for edge in graph.edges:
            dag.add_edge(
                edge.source,
                edge.target,
            )

        try:
            pos = graphviz_layout(
                dag,
                prog="dot",
            )
        except Exception:
            pos = nx.spring_layout(
                dag,
                seed=42,
            )
        

        colors = [
            dag.nodes[node]["color"]
            for node in dag.nodes
        ]

        sizes = [
            dag.nodes[node]["size"]
            for node in dag.nodes
        ]

        labels = {
            node: dag.nodes[node]["label"]
            for node in dag.nodes
        }

        plt.figure(
            figsize=(16,9)
        )

        nx.draw_networkx_nodes(
            dag,
            pos,
            node_color=colors,
            node_size=sizes,
        )

        nx.draw_networkx_edges(
            dag,
            pos,
            arrows=True,
            arrowsize=20,
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