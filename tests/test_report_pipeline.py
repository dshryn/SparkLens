from report import (
    ReportGenerator,
    MarkdownRenderer,
    HTMLRenderer,
)
from report.models import (
    Report,
    ReportFinding,
)

from models.analysis_finding import AnalysisFinding
from models.analysis_report import AnalysisReport
from models.analysis_result import AnalysisResult
from models.execution_dag import ExecutionDAG

from models.enums import (
    Severity,
    OperatorType,
    TransformationType,
)

from models.physical_operator import PhysicalOperator

from ai.models import AIExplanation


def test_report_module_imports():
    assert ReportGenerator is not None
    assert MarkdownRenderer is not None
    assert HTMLRenderer is not None


def test_markdown_renderer():
    report = Report(
        title="SparkLens Analysis Report",
        summary="Test summary",
        findings=[
            ReportFinding(
                title="Shuffle Detected",
                description="A shuffle operation was found.",
                severity="HIGH",
            )
        ],
    )

    markdown = MarkdownRenderer().render(report)

    assert "# SparkLens Analysis Report" in markdown
    assert "Test summary" in markdown
    assert "Shuffle Detected" in markdown


def test_html_renderer():
    report = Report(
        title="SparkLens Analysis Report",
        summary="Test summary",
        findings=[
            ReportFinding(
                title="Shuffle Detected",
                description="A shuffle operation was found.",
                severity="HIGH",
            )
        ],
    )

    html = HTMLRenderer().render(report)

    assert "<html>" in html
    assert "SparkLens Analysis Report" in html
    assert "Shuffle Detected" in html


def test_report_generator():
    operator = PhysicalOperator(
        operator_id=1,
        name="Exchange",
        operator_type=OperatorType.EXCHANGE,
        transformation=TransformationType.WIDE,
    )

    dag = ExecutionDAG()
    dag.add_operator(operator)

    finding = AnalysisFinding(
        rule="shuffle_rule",
        title="Shuffle Detected",
        description="A shuffle operation was found.",
        severity=Severity.HIGH,
        operator_id=1,
    )

    report = AnalysisReport()
    report.add_finding(finding)

    analysis_result = AnalysisResult(
        dag=dag,
        report=report,
    )

    explanation = AIExplanation(
        summary="Execution contains one shuffle.",
        explanation="Shuffle causes data movement.",
        recommendations=[
            "Reduce unnecessary shuffles."
        ],
        model="test-model",
    )

    generated_report = ReportGenerator().generate(
        analysis_result,
        explanation,
    )

    assert generated_report.title == "SparkLens Analysis Report"

    assert generated_report.summary == (
        "Execution contains one shuffle."
    )

    assert len(generated_report.findings) == 1

    assert (
        generated_report.findings[0].title
        == "Shuffle Detected"
    )