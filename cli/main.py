from pathlib import Path
import argparse
import sys

from dotenv import load_dotenv

from services.pipeline import AnalysisPipeline

from report.markdown import MarkdownRenderer
from report.html import HTMLRenderer
from report.exporters import pipeline_to_json

from visualization.dag import DAGVisualizer


load_dotenv()


def analyze_command(
    plan_file: str,
    use_ai: bool,
    use_json: bool = False,
) -> None:

    plan_path = Path(plan_file)

    if not plan_path.exists():

        print(
            f"Plan file not found: {plan_path}",
            file=sys.stderr
        )

        return

    plan = plan_path.read_text(
        encoding="utf-8"
    )

    pipeline = AnalysisPipeline()

    result = pipeline.run(
        plan,
        enable_ai=use_ai,
    )

    if use_json:
        print(pipeline_to_json(result))
        return

    DAGVisualizer().save(
        result.analysis.dag,
        result.analysis.report,
        "dag.png",
    )

    MarkdownRenderer().save(
        result.report,
        "report.md",
    )

    HTMLRenderer().save(
        result.report,
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

    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Output the pipeline result in JSON format"
    )

    args = parser.parse_args()

    if args.command == "analyze":

        analyze_command(
            args.plan_file,
            args.ai,
            args.json,
        )

        return

    parser.print_help()


if __name__ == "__main__":
    main()