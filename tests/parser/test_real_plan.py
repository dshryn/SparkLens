from pathlib import Path

from analyzer.normalizer import PlanNormalizer
from analyzer.parser import PlanParser


def main():
    plan_path = Path("sample_plans/broadcast_join.txt")

    raw_plan = plan_path.read_text(encoding="utf-8")

    normalized_plan = PlanNormalizer().normalize(raw_plan)
    print("=" * 20)
    print("NORMALIZED PLAN")
    print("=" * 20)
    print(normalized_plan)

    parsed = PlanParser().parse(normalized_plan)

    print("=" * 80)
    print("Operators:", len(parsed.operators))
    print("Edges:", len(parsed.edges))
    print("=" * 80)

    for operator in parsed.operators.values():
        print(operator.operator_id, operator.name)

    print("\nReal plan parsed successfully.")


if __name__ == "__main__":
    main()
