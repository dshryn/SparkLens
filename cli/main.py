from pathlib import Path
import argparse

from dotenv import load_dotenv

from services.pipeline import AnalysisPipeline

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

    pipeline = AnalysisPipeline()

    result = pipeline.run(
        plan,
        enable_ai=use_ai,
    )

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