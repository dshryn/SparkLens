from dataclasses import dataclass


@dataclass
class DashboardResult:
    summary: dict
    findings: list
    recommendations: list
    ai_summary: str


def analyze_execution_plan(plan_text: str) -> DashboardResult:
    return DashboardResult(
        summary={
            "operators": 32,
            "joins": 4,
            "shuffles": 3,
            "complexity": "High"
        },
        findings=[
            {
                "severity": "High",
                "rule": "Shuffle Rule",
                "description": "Multiple shuffle exchanges detected."
            },
            {
                "severity": "Medium",
                "rule": "Broadcast Join Rule",
                "description": "Broadcast join opportunity found."
            }
        ],
        recommendations=[
            "Enable AQE.",
            "Consider broadcasting the smaller table.",
            "Reduce unnecessary shuffle operations."
        ],
        ai_summary="""
The execution plan contains several shuffle-heavy operations.
Optimizing join strategies and enabling AQE may significantly improve performance.
"""
    )