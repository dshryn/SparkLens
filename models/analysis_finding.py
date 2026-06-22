from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseModel
from .enums import Severity


@dataclass(slots=True)
class AnalysisFinding(BaseModel):
    """
    Represents a single deterministic insight produced by a rule.

    Each finding describes one observation about the execution plan,
    along with its severity and the operator responsible.
    """

    rule: str
    title: str
    description: str
    severity: Severity
    operator_id: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)