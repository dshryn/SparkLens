from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseModel


@dataclass(slots=True)
class ExecutionStatistics(BaseModel):
    """
    Deterministic summary statistics for a Spark execution plan.

    This model is AI-independent and serves as the canonical execution
    summary for SparkLens. It can be consumed by reports, AI prompt
    generation, dashboards, APIs, and future analysis modules without
    requiring recomputation.
    """

    # ------------------------------------------------------------------
    # Graph statistics
    # ------------------------------------------------------------------

    operator_count: int = 0
    edge_count: int = 0

    root_node_count: int = 0
    leaf_node_count: int = 0

    max_depth: int = 0

    # ------------------------------------------------------------------
    # Execution statistics
    # ------------------------------------------------------------------

    stage_count: int = 0

    join_count: int = 0
    broadcast_join_count: int = 0

    shuffle_count: int = 0
    exchange_count: int = 0

    aggregate_count: int = 0
    sort_count: int = 0
    filter_count: int = 0
    scan_count: int = 0
    window_count: int = 0

    # ------------------------------------------------------------------
    # Rule summary
    # ------------------------------------------------------------------

    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0

    # ------------------------------------------------------------------
    # Complexity
    # ------------------------------------------------------------------

    complexity_score: float = 0.0
    complexity: str = "LOW"

    # ------------------------------------------------------------------
    # Breakdowns
    # ------------------------------------------------------------------

    operator_types: dict[str, int] = field(default_factory=dict)

    transformations: dict[str, int] = field(default_factory=dict)

    join_strategies: dict[str, int] = field(default_factory=dict)