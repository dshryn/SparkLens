from analyzer.analyzer import SparkAnalyzer
from visualization.dag import DAGVisualizer


def test_complete_workflow():
    plan = """
== Physical Plan ==
AdaptiveSparkPlan (7)
+- Project (6)
   +- Filter (5)
      +- Exchange (4)
         +- HashAggregate (3)
            +- Project (2)
               +- Scan parquet (1)
"""

    analyzer = SparkAnalyzer()

    result = analyzer.analyze_plan(plan)

    assert result.dag is not None
    assert result.report is not None

    visualizer = DAGVisualizer()
    visualizer.visualize(
        result.dag,
        result.report,
    )