from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseModel


@dataclass(slots=True)
class ExecutionStatistics(BaseModel):
    """
    Deterministic summary statistics for a parsed execution plan.

    This model is intentionally AI-independent and can be reused by
    PromptBuilder, ReportGenerator, future CostModel, AQE analysis,
    and other analysis modules.
    """

    operator_count: int = 0
    edge_count: int = 0

    root_node_count: int = 0
    leaf_node_count: int = 0

    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    critical_findings: int = 0

    operator_types: dict[str, int] = field(default_factory=dict)

    join_strategies: dict[str, int] = field(default_factory=dict)

    transformations: dict[str, int] = field(default_factory=dict)