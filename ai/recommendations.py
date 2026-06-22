from models.analysis_report import AnalysisReport


class RecommendationEngine:
    """
    Generates deterministic optimization recommendations
    from SparkLens analysis findings.
    """

    _RULE_RECOMMENDATIONS = {
        "Broadcast Join": (
            "Consider broadcasting the smaller dataset to reduce shuffle overhead."
        ),
        "Shuffle": (
            "Review partitioning strategy to minimize expensive shuffle operations."
        ),
        "Exchange": (
            "Avoid unnecessary data exchanges by reducing repartitioning where possible."
        ),
        "Aggregation": (
            "Ensure aggregation keys have suitable cardinality and consider pre-aggregation."
        ),
        "Partition": (
            "Review the partition count to avoid data skew or excessive task overhead."
        ),
        "Sort": (
            "Verify that sorting is required and avoid redundant sort operations."
        ),
        "AQE": (
            "Adaptive Query Execution is enabled. Ensure Spark can leverage runtime optimizations."
        ),
        "Performance": (
            "Review the execution plan for potential bottlenecks highlighted by SparkLens."
        ),
        "Pipeline": (
            "Simplify complex execution pipelines where possible to improve maintainability."
        ),
    }

    @classmethod
    def generate(cls, report: AnalysisReport) -> list[str]:
        recommendations = []

        seen = set()

        for finding in report.findings:
            recommendation = cls._RULE_RECOMMENDATIONS.get(finding.rule)

            if recommendation and recommendation not in seen:
                recommendations.append(recommendation)
                seen.add(recommendation)

        if not recommendations:
            recommendations.append(
                "No optimization recommendations were generated from the current analysis."
            )

        return recommendations