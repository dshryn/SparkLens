from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_sample_plan(name: str) -> str:
    """
    Load a sample Spark physical plan.

    Example:
        plan = load_sample_plan("broadcast_join")
    """

    plan_path = (
        PROJECT_ROOT
        / "sample_plans"
        / f"{name}.txt"
    )

    if not plan_path.exists():
        raise FileNotFoundError(
            f"Sample plan '{name}' not found."
        )

    return plan_path.read_text(encoding="utf-8")