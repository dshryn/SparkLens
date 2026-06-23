from pathlib import Path
import argparse

from analyzer.analyzer import SparkAnalyzer

from report import (
    ReportGenerator,
    MarkdownRenderer,
    HTMLRenderer,
)

from ai.models import AIExplanation


def analyze_command(
    plan_file: str,
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

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_command(
            args.plan_file
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()