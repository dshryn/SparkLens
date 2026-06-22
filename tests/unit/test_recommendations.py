from ai.recommendations import RecommendationEngine
from models.analysis_finding import AnalysisFinding
from models.analysis_report import AnalysisReport
from models.enums import Severity


def test_generate_recommendations():
    report = AnalysisReport()

    report.add_finding(
        AnalysisFinding(
            rule="Shuffle",
            title="Shuffle Detected",
            description="A shuffle operation was detected.",
            severity=Severity.HIGH,
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="Broadcast Join",
            title="Broadcast Join",
            description="Broadcast join was detected.",
            severity=Severity.LOW,
        )
    )

    recommendations = RecommendationEngine.generate(report)

    assert len(recommendations) == 2

    assert any(
        "shuffle" in recommendation.lower()
        for recommendation in recommendations
    )

    assert any(
        "broadcast" in recommendation.lower()
        for recommendation in recommendations
    )