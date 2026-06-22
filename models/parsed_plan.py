from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseModel
from .physical_operator import PhysicalOperator


@dataclass(slots=True)
class ParsedPlan(BaseModel):
    """
    Intermediate representation produced by the execution plan parser.

    Contains parsed operators and their relationships before they are
    converted into an ExecutionDAG.
    """

    operators: dict[int, PhysicalOperator] = field(default_factory=dict)
    edges: list[tuple[int, int]] = field(default_factory=list)