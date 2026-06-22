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