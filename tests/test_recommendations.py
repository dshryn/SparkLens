from ai.recommendations import RecommendationEngine
from models.analysis_finding import AnalysisFinding
from models.analysis_report import AnalysisReport
from models.enums import Severity


def test_generate_recommendations():
    report = AnalysisReport()

    report.add_finding(
        AnalysisFinding(
            rule="ShuffleRule",
            title="Shuffle Detected",
            description="A shuffle operation was detected.",
            severity=Severity.HIGH,
            metadata={
                "positive": False,
                "category": "shuffle",
            },
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="BroadcastJoinRule",
            title="Broadcast Join",
            description="Broadcast join was detected.",
            severity=Severity.LOW,
            metadata={
                "positive": False,
                "category": "broadcast_join",
            },
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