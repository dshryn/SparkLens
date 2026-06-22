from __future__ import annotations

from abc import ABC, abstractmethod

from models.analysis_finding import AnalysisFinding
from models.execution_dag import ExecutionDAG


class Rule(ABC):
    """
    Base class for all SparkLens analysis rules.
    """

    @abstractmethod
    def apply(
        self,
        dag: ExecutionDAG,
    ) -> list[AnalysisFinding]:
        """
        Analyze an execution DAG and return the findings produced by
        this rule.
        """
        raise NotImplementedError