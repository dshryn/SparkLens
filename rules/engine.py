from __future__ import annotations

from models.analysis_report import AnalysisReport
from models.execution_dag import ExecutionDAG

from .base import Rule


class RuleEngine:
    """
    Executes registered analysis rules against an execution DAG.
    """

    # Titles that are considered semantically equivalent when they refer to
    # the same operator. Only the first-registered rule's finding for a
    # given (operator_id, semantic_key) pair is kept; later duplicates are
    # dropped before the report reaches the recommendation engine or the
    # prompt builder.
    _SEMANTIC_TITLE_GROUPS: dict[str, str] = {
        "adaptive query execution detected": "aqe_enabled",
        "aqe enabled": "aqe_enabled",
    }

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
        Execute every registered rule and return the combined, deduplicated
        report.
        """

        report = AnalysisReport()

        for rule in self._rules:
            report.extend(rule.apply(dag))

        report.findings = self._deduplicate(report.findings)

        return report

    @classmethod
    def _deduplicate(
        cls,
        findings: list,
    ) -> list:
        """
        Removes semantically equivalent findings that refer to the same
        operator (e.g. "AQE Enabled" from ExecutionQualityRule and
        "Adaptive Query Execution Detected" from AQERule both describing
        the same AdaptiveSparkPlan operator).

        The first occurrence of a given (operator_id, semantic_key) pair is
        kept; later duplicates are dropped. Findings whose title has no
        registered semantic equivalence are always kept as-is.
        """

        seen: set[tuple[int | None, str]] = set()
        deduplicated = []

        for finding in findings:

            semantic_key = cls._SEMANTIC_TITLE_GROUPS.get(
                finding.title.strip().lower()
            )

            if semantic_key is None:
                # Also treat identical (rule-independent) titles on the
                # same operator as duplicates.
                semantic_key = finding.title.strip().lower()

            dedup_key = (finding.operator_id, semantic_key)

            if dedup_key in seen:
                continue

            seen.add(dedup_key)
            deduplicated.append(finding)

        return deduplicated