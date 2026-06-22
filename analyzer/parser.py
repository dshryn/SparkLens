from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Iterable

from models.enums import OperatorType, TransformationType
from models.parsed_plan import ParsedPlan
from models.physical_operator import PhysicalOperator


# ============================================================================
# Regex Patterns
# ============================================================================

_OPERATOR_HEADER = re.compile(
    r"^\((?P<id>\d+)\)\s+(?P<name>[A-Za-z0-9_]+)$"
)

_PROPERTY_SUFFIX = re.compile(r"\s*\[\d+\]$")

_TREE_NODE = re.compile(
    r"(?P<name>[A-Za-z0-9_]+)\s+\((?P<id>\d+)\)$"
)


# ============================================================================
# Base Parser
# ============================================================================

class BaseParser(ABC):
    """
    Base class for all execution plan parsers.
    """

    @abstractmethod
    def parse(self, lines: Iterable[str]):
        raise NotImplementedError


# ============================================================================
# Node Parser
# ============================================================================

class NodeParser(BaseParser):
    """
    Parses the detailed operator blocks.

    Example

    (10) Project
    Input [1]: ...
    Arguments: ...
    """

    def parse(
        self,
        lines: Iterable[str],
    ) -> dict[int, PhysicalOperator]:

        operators: dict[int, PhysicalOperator] = {}

        current: PhysicalOperator | None = None

        for raw_line in lines:

            line = raw_line.strip()

            if not line:
                continue

            header = _OPERATOR_HEADER.match(line)

            if header:

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

            self._parse_property(current, line)

        return operators

    @staticmethod
    def _parse_property(
        operator: PhysicalOperator,
        line: str,
    ) -> None:

        if ":" not in line:
            return

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        normalized = _PROPERTY_SUFFIX.sub("", key)

        if normalized == "Input":
            operator.inputs.append(value)

        elif normalized == "Output":
            operator.outputs.append(value)

        elif normalized == "Arguments":
            operator.arguments.append(value)

        else:
            operator.metadata[key] = value


# ============================================================================
# Tree Parser
# ============================================================================

class TreeParser(BaseParser):
    """
    Tree reconstruction.

    Implementation will be added in the next commit.
    """

    def parse(
        self,
        lines: Iterable[str],
    ) -> list[tuple[int, int]]:

        return []


# ============================================================================
# High-Level Parser
# ============================================================================

class PlanParser:
    """
    Parses an entire normalized Spark execution plan.
    """

    def __init__(self) -> None:

        self._node_parser = NodeParser()
        self._tree_parser = TreeParser()

    def parse(
        self,
        plan: str,
    ) -> ParsedPlan:

        tree_lines, node_lines = self._split_sections(plan)

        return ParsedPlan(
            operators=self._node_parser.parse(node_lines),
            edges=self._tree_parser.parse(tree_lines),
        )

    @staticmethod
    def _split_sections(
        plan: str,
    ) -> tuple[list[str], list[str]]:

        tree_lines: list[str] = []
        node_lines: list[str] = []

        current = tree_lines

        for line in plan.splitlines():

            if _OPERATOR_HEADER.match(line.strip()):
                current = node_lines

            current.append(line)

        return tree_lines, node_lines