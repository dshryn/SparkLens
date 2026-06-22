from analyzer.normalizer import PlanNormalizer


RAW_PLAN = """
---- Physical Plan ----

PhotonProject (2)

PhotonBroadcastHashJoin (3)

---- Photon Explanation ----
Supported
"""


def main():
    normalizer = PlanNormalizer()

    normalized = normalizer.normalize(RAW_PLAN)

    print(normalized)

    assert "PhotonProject" not in normalized
    assert "PhotonBroadcastHashJoin" not in normalized

    assert "Project" in normalized
    assert "BroadcastHashJoin" in normalized

    assert "Photon Explanation" not in normalized

    print("\nNormalizer test passed.")


if __name__ == "__main__":
    main()