from services.pipeline import AnalysisPipeline, PipelineResult


def analyze_execution_plan(
    plan_text: str,
    enable_ai: bool = True,
) -> PipelineResult:
    """
    Executes the complete SparkLens analysis pipeline and returns
    the PipelineResult for the Streamlit dashboard.
    """

    pipeline = AnalysisPipeline()

    return pipeline.run(
        plan=plan_text,
        enable_ai=enable_ai,
    )