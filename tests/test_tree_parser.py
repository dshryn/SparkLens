from analyzer.parser import TreeParser


TREE = """
AdaptiveSparkPlan (3)
+- Project (2)
   +- Range (1)
"""


def main():
    parser = TreeParser()

    edges = parser.parse(TREE.splitlines())

    print(edges)

    assert (3, 2) in edges
    assert (2, 1) in edges
    assert len(edges) == 2

    print("Tree parser test passed.")


if __name__ == "__main__":
    main()