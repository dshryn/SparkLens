from dataclasses import dataclass

from .analysis_report import AnalysisReport
from .execution_dag import ExecutionDAG


@dataclass(slots=True)
class AnalysisResult:
    """Complete result of a SparkLens analysis."""

    dag: ExecutionDAG
    report: AnalysisReport