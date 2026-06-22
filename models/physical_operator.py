from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseModel
from .enums import OperatorType
from .enums import TransformationType


@dataclass(slots=True)
class PhysicalOperator(BaseModel):
    """
    Represents one node in a Spark Physical Execution Plan.
    """

    operator_id: int

    name: str

    operator_type: OperatorType

    transformation: TransformationType

    depth: int

    children: list[int] = field(default_factory=list)

    metrics: dict[str, float] = field(default_factory=dict)

    metadata: dict[str, str] = field(default_factory=dict)

    tags: list[str] = field(default_factory=list)

    execution_time_ms: float | None = None