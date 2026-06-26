from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseModel


@dataclass(slots=True)
class CostComponent(BaseModel):
    """
    Represents the contribution of a specific execution feature
    to the overall estimated execution cost.
    """

    name: str
    count: int
    weight: int
    score: int
    description: str


@dataclass(slots=True)
class CostEstimate(BaseModel):
    """
    Deterministic estimate of the relative execution complexity
    of a Spark execution plan.

    This is not a runtime prediction. Instead, it provides a
    weighted complexity score derived from execution-plan
    characteristics.
    """

    total_score: int = 0

    components: list[CostComponent] = field(
        default_factory=list
    )

    summary: str = ""

    def add_component(
        self,
        component: CostComponent,
    ) -> None:

        self.components.append(component)
        self.total_score += component.score