"""Styling utilities for graph visualization."""

from models.enums import Severity


class GraphStyle:

    NODE_COLOR = "#4F46E5"
    EDGE_COLOR = "#6B7280"

    SEVERITY_COLORS = {
        Severity.LOW: "#22C55E",
        Severity.MEDIUM: "#FACC15",
        Severity.HIGH: "#F97316",
        Severity.CRITICAL: "#EF4444",
    }

    DEFAULT_NODE_SIZE = 1000
    HIGHLIGHT_NODE_SIZE = 1400

    @classmethod
    def node_color(cls, severity: Severity | None) -> str:
        if severity is None:
            return cls.NODE_COLOR
        return cls.SEVERITY_COLORS[severity]

    @classmethod
    def node_size(cls, highlighted: bool) -> int:
        if highlighted:
            return cls.HIGHLIGHT_NODE_SIZE
        return cls.DEFAULT_NODE_SIZE