from __future__ import annotations

from models.analysis_report import AnalysisReport
from models.execution_dag import ExecutionDAG

from .base import Rule


class RuleEngine:
    """
    Executes registered analysis rules against an execution DAG.
    """

    def __init__(
        self,
        rules: list[Rule] | None = None,
    ) -> None:

        self._rules = rules or []

    def register(
        self,
        rule: Rule,
    ) -> None:
        """
        Register a new rule.
        """

        self._rules.append(rule)

    def run(
        self,
        dag: ExecutionDAG,
    ) -> AnalysisReport:
        """
        Execute every registered rule and return the combined report.
        """

        report = AnalysisReport()

        for rule in self._rules:
            report.extend(rule.apply(dag))

        return report