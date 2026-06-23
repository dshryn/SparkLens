from dataclasses import dataclass, field


@dataclass(slots=True)
class ReportFinding:
    title: str
    description: str
    severity: str
    operator_name: str | None = None


@dataclass(slots=True)
class ReportSection:
    title: str
    content: str


@dataclass(slots=True)
class Report:
    title: str
    summary: str
    findings: list[ReportFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    sections: list[ReportSection] = field(default_factory=list)