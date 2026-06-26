from dataclasses import dataclass


@dataclass
class SummaryCard:
    title: str
    value: str


@dataclass
class FindingRow:
    severity: str
    rule: str
    description: str


@dataclass
class DashboardModel:
    summary_cards: list[SummaryCard]
    findings: list[FindingRow]
    recommendations: list[str]
    ai_summary: str