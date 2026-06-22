from analyzer.analyzer import SparkAnalyzer
from visualization.dag import DAGVisualizer

with open("sample_plans/broadcast_join.txt", encoding="utf-8") as f:
    plan = f.read()

analyzer = SparkAnalyzer()

result = analyzer.analyze_plan(plan)

print(result.report.findings)

visualizer = DAGVisualizer()
visualizer.visualize(result.dag, result.report)