from analyzer.extractor import FormattedPlanExtractor


class MockDataFrame:
    def explain(self, mode="simple"):
        print(
            """
---- Physical Plan ----
PhotonProject (1)

(1) PhotonProject
Arguments: [id]
"""
        )


def main():
    extractor = FormattedPlanExtractor()

    plan = extractor.extract(MockDataFrame())

    print(plan)

    assert "PhotonProject" in plan

    print("\nExtractor test passed.")


if __name__ == "__main__":
    main()