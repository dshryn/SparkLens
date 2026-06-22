from analyzer.parser import PlanParser


PLAN = """
AdaptiveSparkPlan (3)
+- Project (2)
   +- Range (1)

(1) Range
Output [1]: [id]
Arguments: Range

(2) Project
Input [1]: [id]
Arguments: [id]

(3) AdaptiveSparkPlan
Arguments: isFinalPlan=false
"""


def main():

    parser = PlanParser()

    parsed = parser.parse(PLAN)

    print(parsed)

    assert len(parsed.operators) == 3

    assert (3, 2) in parsed.edges
    assert (2, 1) in parsed.edges

    print("Plan parser test passed.")


if __name__ == "__main__":
    main()