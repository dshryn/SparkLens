"""Visualization models for rendering execution graphs."""

from dataclasses import dataclass

from models.enums import OperatorType, Severity


@dataclass(slots=True)
class GraphNode:
    """Represents a node in the visualization graph."""

    id: int
    label: str
    operator_type: OperatorType
    severity: Severity | None = None
    highlighted: bool = False


@dataclass(slots=True)
class GraphEdge:
    """Represents a directed edge in the visualization graph."""

    source: int
    target: int


@dataclass(slots=True)
class GraphModel:
    """Complete visualization graph."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]