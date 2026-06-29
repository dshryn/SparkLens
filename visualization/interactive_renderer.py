"""Interactive DAG renderer using PyVis."""

from __future__ import annotations

from pathlib import Path

from pyvis.network import Network

from models.enums import Severity
from visualization.base_renderer import BaseRenderer
from visualization.models import GraphModel


class InteractiveRenderer(BaseRenderer):
    """
    Renders a GraphModel as an interactive HTML graph using PyVis.
    """

    _SEVERITY_COLORS = {
        Severity.LOW: "#22C55E",
        Severity.MEDIUM: "#FACC15",
        Severity.HIGH: "#F97316",
        Severity.CRITICAL: "#EF4444",
        None: "#4F46E5",
    }

    def _build_network(
        self,
        graph: GraphModel,
    ) -> Network:

        net = Network(
            height="800px",
            width="100%",
            directed=True,
            bgcolor="#FFFFFF",
        )

        net.barnes_hut()

        for node in graph.nodes:

            color = self._SEVERITY_COLORS.get(
                node.severity,
                "#4F46E5",
            )

            title = (
                f"<b>{node.label}</b><br>"
                f"Operator ID: {node.id}<br>"
                f"Type: {node.operator_type.value}"
            )

            if node.severity is not None:
                title += f"<br>Severity: {node.severity.value}"

            net.add_node(
                n_id=node.id,
                label=f"{node.label}\n#{node.id}",
                title=title,
                color=color,
                size=30 if node.highlighted else 22,
            )

        for edge in graph.edges:

            net.add_edge(
                edge.source,
                edge.target,
                arrows="to",
            )

        net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "barnesHut": {
                  "gravitationalConstant": -2500,
                  "centralGravity": 0.2,
                  "springLength": 120
                }
              },
              "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": true
              },
              "edges": {
                "smooth": {
                  "enabled": true,
                  "type": "dynamic"
                }
              }
            }
            """)

        return net

    def render(
        self,
        graph: GraphModel,
    ) -> None:
        """
        Opens the interactive graph in the browser.
        """

        self.save(
            graph,
            "interactive_dag.html",
        )

    def save(
        self,
        graph: GraphModel,
        path: str,
    ) -> None:
        """
        Saves the interactive graph as an HTML file.
        """

        network = self._build_network(graph)

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        network.write_html(
            path,
            notebook=False,
        )
