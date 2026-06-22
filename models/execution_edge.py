from __future__ import annotations

from dataclasses import dataclass

from .base import BaseModel


@dataclass(slots=True)
class ExecutionEdge(BaseModel):
    """
    Represents a directed edge in the Spark execution DAG.

    The edge points from a parent (upstream) physical operator
    to a child (downstream) physical operator.
    """

    parent_id: int
    child_id: int