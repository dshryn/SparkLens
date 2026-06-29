from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .analysis_report import AnalysisReport
from .execution_dag import ExecutionDAG
from .execution_statistics import ExecutionStatistics


@dataclass(slots=True)
class AnalysisResult:
    """
    Complete result of a SparkLens analysis.

    This is the canonical backend model returned by the analyzer and
    consumed by every frontend (CLI, Streamlit, future REST API, etc.).
    All deterministic analysis produced by SparkLens should be surfaced
    through this model to avoid duplicate computation elsewhere.
    """

    # Core analysis artifacts
    dag: ExecutionDAG
    report: AnalysisReport
    statistics: ExecutionStatistics = field(
        default_factory=ExecutionStatistics
    )

    # Future backend artifacts for visualization and advanced analysis.
    # Examples:
    # - critical path
    # - stage boundaries
    # - bottlenecks
    # - expensive operators
    artifacts: dict[str, Any] = field(default_factory=dict)

    # General analysis metadata.
    # Examples:
    # - generated_at
    # - parser_version
    # - adaptive_execution
    # - plan_hash
    metadata: dict[str, Any] = field(default_factory=dict)