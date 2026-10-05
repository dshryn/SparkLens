from models.analysis_finding import AnalysisFinding
from models.analysis_report import AnalysisReport
from models.enums import (
    OperatorType,
    Severity,
    TransformationType,
)
from models.execution_dag import ExecutionDAG
from models.physical_operator import PhysicalOperator

from ai.recommendations import RecommendationEngine
from rules.aggregation_rules import AggregationRule
from rules.quality_rules import ExecutionQualityRule
from rules.stage_rules import StageRule


def make_operator(
    operator_id: int,
    name: str,
    operator_type: OperatorType,
    arguments: list[str] | None = None,
    transformation: TransformationType = (
        TransformationType.NONE
    ),
) -> PhysicalOperator:

    return PhysicalOperator(
        operator_id=operator_id,
        name=name,
        operator_type=operator_type,
        transformation=transformation,
        arguments=arguments or [],
    )


def build_two_phase_aggregation_dag(
    vanilla_final: bool = True,
) -> ExecutionDAG:

    dag = ExecutionDAG()

    final_args = []

    if not vanilla_final:
        final_args = [
            "finalmerge_count"
        ]

    final = make_operator(
        1,
        "HashAggregate",
        OperatorType.HASH_AGGREGATE,
        arguments=final_args,
        transformation=TransformationType.WIDE,
    )

    exchange = make_operator(
        2,
        "Exchange",
        OperatorType.EXCHANGE,
        arguments=[
            "hashpartitioning(key, 200)"
        ],
        transformation=TransformationType.WIDE,
    )

    partial = make_operator(
        3,
        "HashAggregate",
        OperatorType.HASH_AGGREGATE,
        arguments=[
            "partial_count"
        ],
        transformation=TransformationType.WIDE,
    )

    project = make_operator(
        4,
        "Project",
        OperatorType.PROJECT,
        transformation=TransformationType.NARROW,
    )

    filter_operator = make_operator(
        5,
        "Filter",
        OperatorType.FILTER,
        transformation=TransformationType.NARROW,
    )

    range_operator = make_operator(
        6,
        "Range",
        OperatorType.UNKNOWN,
    )

    for operator in (
        final,
        exchange,
        partial,
        project,
        filter_operator,
        range_operator,
    ):
        dag.add_operator(operator)

    # Downstream -> upstream according to ExecutionDAG semantics.
    dag.connect(1, 2)
    dag.connect(2, 3)
    dag.connect(3, 4)
    dag.connect(4, 5)
    dag.connect(5, 6)

    return dag


def test_vanilla_two_phase_aggregation_is_detected():

    dag = build_two_phase_aggregation_dag(
        vanilla_final=True
    )

    findings = ExecutionQualityRule().apply(
        dag
    )

    titles = {
        finding.title
        for finding in findings
    }

    assert "Two-Phase Aggregation" in titles
    assert "Required Shuffle (Aggregation)" in titles


def test_photon_two_phase_aggregation_is_detected():

    dag = build_two_phase_aggregation_dag(
        vanilla_final=False
    )

    findings = ExecutionQualityRule().apply(
        dag
    )

    titles = {
        finding.title
        for finding in findings
    }

    assert "Two-Phase Aggregation" in titles
    assert "Required Shuffle (Aggregation)" in titles


def test_vanilla_final_aggregation_is_structurally_labeled():

    dag = build_two_phase_aggregation_dag(
        vanilla_final=True
    )

    findings = AggregationRule().apply(
        dag
    )

    final_finding = next(
        finding
        for finding in findings
        if finding.operator_id == 1
    )

    assert final_finding.title == (
        "Final Aggregation"
    )


def test_stage_rule_counts_shuffle_boundaries_only():

    dag = build_two_phase_aggregation_dag()

    findings = StageRule().apply(
        dag
    )

    stage_finding = next(
        finding
        for finding in findings
        if finding.title == "Estimated Stage Count"
    )

    assert stage_finding.metadata[
        "stage_count"
    ] == 2


def test_required_shuffle_suppresses_generic_recommendations():

    report = AnalysisReport()

    report.add_finding(
        AnalysisFinding(
            rule="ExecutionQualityRule",
            title="Required Shuffle (Aggregation)",
            description="Required shuffle.",
            severity=Severity.LOW,
            operator_id=2,
            metadata={
                "positive": True,
                "category": (
                    "required_shuffle_aggregation"
                ),
                "required": True,
                "required_operator_id": 2,
            },
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="ShuffleRule",
            title="Shuffle Detected",
            description="Shuffle.",
            severity=Severity.MEDIUM,
            operator_id=2,
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="ExchangeRule",
            title="Exchange Operator",
            description="Exchange.",
            severity=Severity.MEDIUM,
            operator_id=2,
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="PartitionRule",
            title="Hash Partitioning Detected",
            description="Hash partitioning.",
            severity=Severity.MEDIUM,
            operator_id=2,
        )
    )

    recommendations = (
        RecommendationEngine.generate(
            report
        )
    )

    assert len(recommendations) == 1

    assert "No optimization opportunities" in (
        recommendations[0]
    )


def test_two_phase_aggregation_suppresses_aggregation_advice():

    report = AnalysisReport()

    report.add_finding(
        AnalysisFinding(
            rule="ExecutionQualityRule",
            title="Two-Phase Aggregation",
            description="Expected two-phase aggregation.",
            severity=Severity.LOW,
            operator_id=3,
            metadata={
                "positive": True,
                "category": (
                    "two_phase_aggregation"
                ),
            },
        )
    )

    report.add_finding(
        AnalysisFinding(
            rule="AggregationRule",
            title="Aggregation",
            description="Aggregation.",
            severity=Severity.LOW,
            operator_id=1,
        )
    )

    recommendations = (
        RecommendationEngine.generate(
            report
        )
    )

    assert len(recommendations) == 1

    assert "No optimization opportunities" in (
        recommendations[0]
    )


def test_multiple_required_shuffles_do_not_create_generic_shuffle_advice():

    report = AnalysisReport()

    for operator_id in (10, 11):

        report.add_finding(
            AnalysisFinding(
                rule="ExecutionQualityRule",
                title="Required Shuffle (Aggregation)",
                description="Required.",
                severity=Severity.LOW,
                operator_id=operator_id,
                metadata={
                    "positive": True,
                    "category": (
                        "required_shuffle_aggregation"
                    ),
                    "required": True,
                    "required_operator_id": operator_id,
                },
            )
        )

    report.add_finding(
        AnalysisFinding(
            rule="PerformanceRule",
            title="Multiple Shuffle Operations",
            description="Multiple shuffles.",
            severity=Severity.MEDIUM,
            metadata={
                "shuffle_operator_ids": [
                    10,
                    11,
                ],
            },
        )
    )

    recommendations = (
        RecommendationEngine.generate(
            report
        )
    )

    assert len(recommendations) == 1

    assert "No optimization opportunities" in (
        recommendations[0]
    )