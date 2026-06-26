from pathlib import Path
import argparse
import os

from dotenv import load_dotenv

from ai.providers.retrying_provider import RetryingProvider
from analyzer.analyzer import SparkAnalyzer

from ai.explainer import Explainer
from ai.models import AIConfig
from ai.models import AIExplanation
from ai.providers.gemini_provider import GeminiProvider

from report.generator import ReportGenerator
from report.markdown import MarkdownRenderer
from report.html import HTMLRenderer

from visualization.dag import DAGVisualizer


load_dotenv()


def analyze_command(
    plan_file: str,
    use_ai: bool,
) -> None:

    plan_path = Path(plan_file)

    if not plan_path.exists():
        print(
            f"Plan file not found: {plan_path}"
        )
        return

    plan = plan_path.read_text(
        encoding="utf-8"
    )

    analyzer = SparkAnalyzer()

    analysis = analyzer.analyze_plan(
        plan
    )

    visualizer = DAGVisualizer()

    visualizer.save(
        analysis.dag,
        analysis.report,
        "dag.png",
    )

    if use_ai:

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            print(
                "GEMINI_API_KEY not found."
            )
            return

        provider = RetryingProvider(
            GeminiProvider(
                AIConfig(
                    api_key=api_key,
                )
            ),
            max_attempts=3,
            initial_delay=1.0,
        )

        explainer = Explainer(
            provider
        )

        explanation = explainer.explain(
            analysis
        )

    else:

        explanation = AIExplanation(
            summary="AI explanation not generated.",
            explanation=(
                "CLI currently runs deterministic "
                "analysis only."
            ),
            recommendations=[],
            model="none",
        )

    report = ReportGenerator().generate(
        analysis,
        explanation,
    )

    MarkdownRenderer().save(
        report,
        "report.md",
    )

    HTMLRenderer().save(
        report,
        "report.html",
    )

    print("Generated dag.png")
    print("Generated report.md")
    print("Generated report.html")


def main():

    parser = argparse.ArgumentParser(
        prog="sparklens",
    )

    subparsers = parser.add_subparsers(
        dest="command",
    )

    analyze_parser = subparsers.add_parser(
        "analyze"
    )

    analyze_parser.add_argument(
        "plan_file"
    )

    analyze_parser.add_argument(
        "--ai",
        action="store_true",
    )

    args = parser.parse_args()

    if args.command == "analyze":

        analyze_command(
            args.plan_file,
            args.ai,
        )

        return

    parser.print_help()


if __name__ == "__main__":
    main()