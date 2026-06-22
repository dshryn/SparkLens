from __future__ import annotations

import io
from contextlib import redirect_stdout
from typing import Protocol


class ExplainableDataFrame(Protocol):
    """Any object capable of producing a Spark explain plan."""

    def explain(self, mode: str = "simple") -> None:
        ...


class PlanExtractor(Protocol):
    """Interface implemented by all execution plan extractors."""

    def extract(self, dataframe: ExplainableDataFrame) -> str:
        ...


class FormattedPlanExtractor:
    """
    Extracts the formatted Spark physical execution plan.

    Compatible with Databricks Community Edition.
    """

    def extract(self, dataframe: ExplainableDataFrame) -> str:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            dataframe.explain(mode="formatted")

        return buffer.getvalue().strip()