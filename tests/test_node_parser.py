from analyzer.parser import NodeParser


PLAN = """
(1) Range
Output [1]: [id]
Arguments: Range (0,100)

(2) Project
Input [1]: [id]
Arguments: [id % 10]

(3) BroadcastHashJoin
Left keys [1]: [id]
Right keys [1]: [value]
Join type: Inner
"""


def main():
    parser = NodeParser()

    operators = parser.parse(PLAN.splitlines())

    assert len(operators) == 3

    assert operators[1].name == "Range"

    assert operators[2].inputs

    assert operators[3].metadata["Join type"] == "Inner"

    print("Node parser test passed.")


if __name__ == "__main__":
    main()