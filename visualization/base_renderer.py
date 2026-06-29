from __future__ import annotations

from typing import Protocol

from visualization.models import GraphModel


class BaseRenderer(Protocol):
    """
    Common interface implemented by all visualization renderers.
    """

    def render(
        self,
        graph: GraphModel,
    ) -> None: ...

    def save(
        self,
        graph: GraphModel,
        path: str,
    ) -> None: ...
