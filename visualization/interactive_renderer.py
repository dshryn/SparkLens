"""Interactive DAG renderer using PyVis."""

from __future__ import annotations

from pathlib import Path

from altair import Color
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
            bgcolor="#111827",
        )

        net.barnes_hut(
            gravity=-4000,
            central_gravity=0.25,
            spring_length=140,
            spring_strength=0.03,
            damping=0.09,
        )

        for node in graph.nodes:

            color = self._SEVERITY_COLORS.get(
                node.severity,
                "#4F46E5",
            )

            title = (
                f"<h3>{node.label}</h3>"
                f"<b>Operator ID:</b> {node.id}<br>"
                f"<b>Type:</b> {node.operator_type.value}"
            )

            if node.severity is not None:
                title += f"<br><b>Severity:</b> " f"{node.severity.value}"

            net.add_node(
                n_id=node.id,
                label=node.label,
                title=title,
                color=color,
                borderWidth=2,
                borderWidthSelected=4,
                shape="box",
                font={
                    "color": "white",
                    "size": 18,
                    "face": "Arial",
                },
                margin=12,
                size=35 if node.highlighted else 28,
            )

        for edge in graph.edges:

            net.add_edge(
                edge.source,
                edge.target,
                arrows="to",
                color="#94A3B8",
                width=2,
                smooth={
                    "enabled": True,
                    "type": "cubicBezier",
                },
            )

        net.set_options("""
            var options = {
              "layout": {
                "improvedLayout": true
              },
              "interaction": {
                "hover": true,
                "tooltipDelay": 150,
                "dragNodes": true,
                "dragView": true,
                "zoomView": true,
                "keyboard": true,
                "navigationButtons": true,
                "multiselect": true
              },
              "physics": {
                "enabled": true,
                "barnesHut": {
                  "gravitationalConstant": -4000,
                  "centralGravity": 0.25,
                  "springLength": 140,
                  "springConstant": 0.03,
                  "damping": 0.09
                },
                "minVelocity": 0.75
              },
              "nodes": {
                "shadow": true
              },
              "edges": {
                "shadow": false,
                "smooth": {
                  "enabled": true,
                  "type": "dynamic"
                }
              }
            }
            """)

        return net

    def to_html(
        self,
        graph: GraphModel,
    ) -> str:
        """
        Returns the interactive graph as an HTML string.
        """

        network = self._build_network(
            graph,
        )

        return network.generate_html()

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

        network = self._build_network(
            graph,
        )

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        network.write_html(
            path,
            notebook=False,
        )
