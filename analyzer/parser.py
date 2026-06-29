from __future__ import annotations
import re
from typing import Iterable

from models.enums import OperatorType, TransformationType
from models.parsed_plan import ParsedPlan
from models.physical_operator import PhysicalOperator

# ------------------------------------------------------------------------
# Regex Patterns
# ------------------------------------------------------------------------

# Matches lines like "(123) OperatorName"
_OPERATOR_HEADER = re.compile(r"^\((?P<id>\d+)\)\s+(?P<name>[A-Za-z0-9_]+)")
# Strips trailing index suffixes (rarely needed here)
_PROPERTY_SUFFIX = re.compile(r"\s*\[\d+\]$")


# ------------------------------------------------------------------------
# Node Parser
# ------------------------------------------------------------------------
class NodeParser:
    """
    Parses the detailed operator blocks into PhysicalOperator instances.
    """

    def parse(self, lines: Iterable[str]) -> dict[int, PhysicalOperator]:
        operators: dict[int, PhysicalOperator] = {}
        current: PhysicalOperator | None = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            header = _OPERATOR_HEADER.match(line)
            if header:
                # Start of a new operator block: e.g. "(10) Project"
                operator_id = int(header.group("id"))
                operator_name = header.group("name")
                current = PhysicalOperator(
                    operator_id=operator_id,
                    name=operator_name,
                    operator_type=OperatorType.UNKNOWN,
                    transformation=TransformationType.NONE,
                )
                operators[operator_id] = current
                continue

            if current is None:
                continue

            # Parse properties into operator fields
            if ":" in line:
                key, value = map(str.strip, line.split(":", 1))
                normalized = _PROPERTY_SUFFIX.sub("", key).strip()
                if normalized == "Input":
                    current.inputs.append(value)
                elif normalized == "Output":
                    current.outputs.append(value)
                elif normalized == "Arguments":
                    current.arguments.append(value)
                else:
                    current.metadata[key] = value

        return operators


# ------------------------------------------------------------------------
# Tree Parser
# ------------------------------------------------------------------------
class TreeParser:
    """
    Reconstructs the parent-child edges from the plan's ASCII-art tree.

    Scans each line of the plan tree, infers indent level by the first letter
    position, and uses a stack to assign parent→child relationships. Skips
    header lines (== Physical Plan ==, etc.).
    """

    def parse(self, lines: Iterable[str]) -> list[tuple[int, int]]:
        edges: list[tuple[int, int]] = []
        stack: list[tuple[int, int]] = []  # (node_id, indent)

        for raw_line in lines:
            line = raw_line.rstrip()
            # Skip empty or header lines (e.g. "== Physical Plan ==", sections)
            if not line.strip() or "==" in line:
                continue

            # Try to find an operator ID in parentheses at line end
            id_match = re.search(r"\((\d+)\)\s*$", line)
            if not id_match:
                continue
            node_id = int(id_match.group(1))

            # Find the position of the first letter of the operator name
            alpha_match = re.search(r"[A-Za-z]", line)
            if not alpha_match:
                continue
            indent = alpha_match.start()

            # Pop stack to find current parent
            while stack and stack[-1][1] >= indent:
                stack.pop()
            # The new parent is the current top of stack (if any)
            if stack:
                parent_id = stack[-1][0]
                edges.append((parent_id, node_id))

            # Push this node onto the stack
            stack.append((node_id, indent))

        return edges


# ------------------------------------------------------------------------
# High-Level Parser
# ------------------------------------------------------------------------
class PlanParser:
    """
    Parses a full Spark execution plan string into a ParsedPlan.
    """

    def __init__(self) -> None:
        self._node_parser = NodeParser()
        self._tree_parser = TreeParser()

    def parse(self, plan: str) -> ParsedPlan:
        """
        Splits the plan text into the tree (outline) and node-detail sections,
        then produces a ParsedPlan(operators, edges).
        """
        tree_lines: list[str] = []
        node_lines: list[str] = []
        current = tree_lines

        # Separate the tree part from the operator detail part
        for line in plan.splitlines():
            if _OPERATOR_HEADER.match(line.strip()):
                current = node_lines  # switch to reading operator blocks
            current.append(line)

        # Parse nodes first
        operators = self._node_parser.parse(node_lines)

        # Classify each operator by name (substring matches)
        for op in operators.values():
            name = op.name
            # Map name substrings to OperatorType
            if "BroadcastHashJoin" in name:
                op.operator_type = OperatorType.BROADCAST_HASH_JOIN
                op.transformation = TransformationType.WIDE
                # Mark broadcast hint
                op.metadata["broadcast_join"] = "true"
            elif "ShuffleHashJoin" in name:
                op.operator_type = OperatorType.SHUFFLE_HASH_JOIN
                op.transformation = TransformationType.WIDE
            elif "SortMergeJoin" in name:
                op.operator_type = OperatorType.SORT_MERGE_JOIN
                op.transformation = TransformationType.WIDE
            elif "HashAggregate" in name or "GroupingAgg" in name:
                op.operator_type = OperatorType.HASH_AGGREGATE
                op.transformation = TransformationType.WIDE
            elif "SortAggregate" in name or "SortMergeAggregate" in name:
                op.operator_type = OperatorType.SORT_AGGREGATE
                op.transformation = TransformationType.WIDE
            elif "ShuffleExchange" in name or "BroadcastExchange" in name:
                if "BroadcastExchange" in name:
                    op.operator_type = OperatorType.BROADCAST_EXCHANGE
                else:
                    op.operator_type = OperatorType.EXCHANGE
                op.transformation = TransformationType.WIDE
            elif "Sort" in name:
                op.operator_type = OperatorType.SORT
                op.transformation = TransformationType.WIDE
            elif "Project" in name:
                op.operator_type = OperatorType.PROJECT
                op.transformation = TransformationType.NARROW
            elif "Filter" in name:
                op.operator_type = OperatorType.FILTER
                op.transformation = TransformationType.NARROW
            elif "FileScan" in name or "Scan" in name:
                op.operator_type = OperatorType.FILE_SCAN
                op.transformation = TransformationType.NARROW
            else:
                # Leave as UNKNOWN/NONE
                op.operator_type = OperatorType.UNKNOWN
                if op.transformation == TransformationType.NONE:
                    # If still NONE, default narrow for safe side
                    op.transformation = TransformationType.NARROW

        # Parse tree edges
        edges = self._tree_parser.parse(tree_lines)
        return ParsedPlan(operators=operators, edges=edges)
