from __future__ import annotations

from dataclasses import dataclass, field

from .analysis_finding import AnalysisFinding
from .base import BaseModel


@dataclass(slots=True)
class AnalysisReport(BaseModel):
    """
    Represents the complete deterministic analysis of a Spark execution plan.

    Produced by the RuleEngine and consumed by the visualization and AI
    layers.
    """

    findings: list[AnalysisFinding] = field(default_factory=list)

    def add_finding(
        self,
        finding: AnalysisFinding,
    ) -> None:
        self.findings.append(finding)

    def extend(
        self,
        findings: list[AnalysisFinding],
    ) -> None:
        self.findings.extend(findings)

    def has_findings(self) -> bool:
        return len(self.findings) > 0

    def findings_by_severity(
        self,
        severity,
    ) -> list[AnalysisFinding]:
        return [
            finding
            for finding in self.findings
            if finding.severity == severity
        ]

    def findings_for_operator(
        self,
        operator_id: int,
    ) -> list[AnalysisFinding]:
        return [
            finding
            for finding in self.findings
            if finding.operator_id == operator_id
        ]