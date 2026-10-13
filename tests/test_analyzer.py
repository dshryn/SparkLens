from analyzer.analyzer import SparkAnalyzer


def test_full_analysis():

    plan = """
    ---- Physical Plan ----
    PhotonProject (1)

    (1) PhotonProject
    Arguments: [id]
    """

    analyzer = SparkAnalyzer()

    report = analyzer.analyze_plan(plan)

    assert report is not None


def test_nyc_cab_surge_plan_can_be_analyzed():
    from pathlib import Path

    plan_path = Path("sample_plans/nyc_cab_surge_training.txt")
    assert plan_path.exists(), "Sample plan nyc_cab_surge_training.txt must exist"

    plan = plan_path.read_text(encoding="utf-8")
    result = SparkAnalyzer().analyze_plan(plan)

    assert result is not None
    assert result.report is not None
    assert result.dag is not None
    assert len(result.dag.operators) > 0
    assert len(result.report.findings) > 0