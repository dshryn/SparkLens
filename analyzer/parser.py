from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable

from models.enums import OperatorType, TransformationType
from models.parsed_plan import ParsedPlan
from models.physical_operator import PhysicalOperator

_OPERATOR_HEADER = re.compile(r"^\((?P<id>\d+)\)\s+(?P<name>[A-Za-z0-9_]+)")
_PROPERTY_SUFFIX = re.compile(r"\s*\[\d+\]$")
_TRAILING_ID = re.compile(r"\((\d+)\)\s*$")

_CONNECTOR_UNIT_PATTERNS = [
    re.compile(r"^:(\s*)"),
    re.compile(r"^\+-\s*"),
    re.compile(r"^├─\s*"),
    re.compile(r"^└─\s*"),
    re.compile(r"^│\s*"),
    re.compile(r"^\s{3}"),
]


@dataclass(frozen=True)
class RealTreeToken:
    """
    A tree line that corresponds to an actual PhysicalOperator: it carries a
    numbered id and will have a matching entry in NodeParser's output.
    node_id is a plain `int` -- never Optional -- so any code holding a
    RealTreeToken can pass its node_id directly wherever an int id is
    required, with no narrowing, cast, or assertion needed.
    """

    depth: int
    name: str
    node_id: int
    raw_line: str


@dataclass(frozen=True)
class WrapperTreeToken:
    """
    A tree line that is structural scaffolding only (AdaptiveSparkPlan,
    ResultStage, ShuffleMapStage, BroadcastQueryStage, WholeStageCodegen,
    ...). These appear in Spark's textual tree but are never assigned a
    numbered id and never appear in the detail block section -- they are
    NOT PhysicalOperators and are intentionally excluded from
    ParsedPlan.operators. There is no node_id field at all: the type system
    itself prevents a WrapperTreeToken from ever being used as an edge
    endpoint, rather than relying on a runtime None-check.
    """

    depth: int
    name: str
    raw_line: str


# A tree line is always exactly one of these two kinds. Code that needs to
# treat both uniformly (e.g. depth-stack management) can rely on `depth`
# being present on both members of the union; code that needs a real id
# narrows with `isinstance(token, RealTreeToken)`, after which `token.node_id`
# is a plain `int` to the type checker -- no cast, no ignore, no assert.
TreeToken = RealTreeToken | WrapperTreeToken


class TreeLexer:
    """
    Converts raw ASCII-tree lines into TreeTokens. Indentation is measured
    in whole connector units consumed from the front of the line, not by
    locating the first alphabetic character -- robust to Unicode glyphs,
    ASCII fallback glyphs, and their differing display widths.
    """

    def _measure_depth(self, line: str) -> tuple[int, str]:
        depth = 0
        remainder = line
        progressed = True
        while progressed:
            progressed = False
            for pattern in _CONNECTOR_UNIT_PATTERNS:
                match = pattern.match(remainder)
                if match:
                    remainder = remainder[match.end():]
                    depth += 1
                    progressed = True
                    break
        return depth, remainder

    def lex(self, lines: Iterable[str]) -> list[TreeToken]:
        tokens: list[TreeToken] = []

        for raw_line in lines:
            line = raw_line.rstrip()
            if not line.strip():
                continue
            if "== " in line and " ==" in line:
                continue  # section header, e.g. "== Physical Plan =="

            depth, remainder = self._measure_depth(line)

            name_match = re.search(r"[A-Za-z][A-Za-z0-9_]*", remainder)
            if not name_match:
                continue  # connector-only line, genuinely not a node

            name = name_match.group(0)
            id_match = _TRAILING_ID.search(line)

            token: TreeToken
            if id_match:
                token = RealTreeToken(
                    depth=depth, name=name, node_id=int(id_match.group(1)), raw_line=line
                )
            else:
                token = WrapperTreeToken(depth=depth, name=name, raw_line=line)

            tokens.append(token)

        return tokens


class NodeParser:
    """Parses the numbered operator detail blocks into PhysicalOperator instances.

    This is the single source of truth for which ids exist in ParsedPlan.operators.
    EdgeBuilder is constrained to only ever reference ids that could have come
    from here, by construction (see EdgeBuilder).
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


class EdgeBuilder:
    """
    Builds parent-child edges from token depth.

    Wrapper tokens (node_id is None) are pushed onto the depth stack so
    that depth is measured correctly for their descendants, but they are
    NEVER used as an edge endpoint in either direction:

      - A wrapper token itself never appears as a child in an emitted edge.
      - When looking for a token's parent, the stack is walked upward past
        any wrapper tokens until a real (node_id is not None) token is
        found, or the stack is exhausted (token is a true root).

    This guarantees, by construction, that every edge in the returned list
    references only ids that exist in the operators dict produced by
    NodeParser, since both node_id here and NodeParser's operator_id are
    parsed from the same "(id)" token format.

    A useful side effect: when a wrapper sits directly between two real
    operators (e.g. ShuffleExchangeSource -> ShuffleMapStage ->
    ShuffleExchangeSink), the wrapper is transparently skipped and the two
    real operators are connected directly -- which is also the correct
    "single logical shuffle boundary" semantics.
    """

    def build(self, tokens: list[TreeToken]) -> list[tuple[int, int]]:
        edges: list[tuple[int, int]] = []
        stack: list[TreeToken] = []

        for token in tokens:
            while stack and stack[-1].depth >= token.depth:
                stack.pop()

            if isinstance(token, RealTreeToken):
                ancestor = self._nearest_real_ancestor(stack)
                if ancestor is not None:
                    # Both operands are plain `int` here: token.node_id is
                    # `int` because `token` was narrowed to RealTreeToken by
                    # the isinstance check above, and ancestor.node_id is
                    # `int` because _nearest_real_ancestor's return type is
                    # `RealTreeToken | None`. No cast or assert is needed.
                    edges.append((ancestor.node_id, token.node_id))

            stack.append(token)

        return edges

    @staticmethod
    def _nearest_real_ancestor(stack: list[TreeToken]) -> RealTreeToken | None:
        for token in reversed(stack):
            if isinstance(token, RealTreeToken):
                return token
        return None


class TreeParser:
    """
    Public API preserved: TreeParser.parse(lines) -> list[tuple[int, int]]
    Every returned tuple references only ids present in NodeParser's output.
    """

    def __init__(self) -> None:
        self._lexer = TreeLexer()
        self._edge_builder = EdgeBuilder()

    def parse(self, lines: Iterable[str]) -> list[tuple[int, int]]:
        tokens = self._lexer.lex(lines)
        return self._edge_builder.build(tokens)

    def parse_tokens(self, lines: Iterable[str]) -> list[TreeToken]:
        """Exposes tokens (including wrapper tokens) for read-only semantic
        passes, e.g. shuffle-boundary detection for stats/labeling."""
        return self._lexer.lex(lines)


@dataclass
class ShuffleBoundary:
    sink_id: int
    source_id: int
    stage_wrapper_name: str


class ShuffleBoundaryDetector:
    """
    Read-only detector for stats/labeling purposes only. It does NOT modify
    edges -- EdgeBuilder already produces the correct connectivity by
    transparently skipping the ShuffleMapStage wrapper. This pass exists so
    the analyzer can report "1 shuffle boundary" instead of miscounting
    ShuffleExchangeSink and ShuffleExchangeSource as two unrelated exchanges.
    """

    def detect(self, tokens: list[TreeToken]) -> list[ShuffleBoundary]:
        boundaries: list[ShuffleBoundary] = []

        for i, token in enumerate(tokens):
            if not isinstance(token, RealTreeToken) or token.name != "ShuffleExchangeSource":
                continue
            for j in range(i + 1, len(tokens)):
                stage_token = tokens[j]
                if stage_token.depth <= token.depth:
                    break
                if isinstance(stage_token, WrapperTreeToken) and stage_token.depth == token.depth + 1:
                    for sink_token in tokens[j + 1:]:
                        if sink_token.depth <= stage_token.depth:
                            break
                        if (
                            isinstance(sink_token, RealTreeToken)
                            and sink_token.name == "ShuffleExchangeSink"
                            and sink_token.depth == stage_token.depth + 1
                        ):
                            boundaries.append(
                                ShuffleBoundary(
                                    sink_id=sink_token.node_id,
                                    source_id=token.node_id,
                                    stage_wrapper_name=stage_token.name,
                                )
                            )
                    break

        return boundaries


class PlanParser:
    def __init__(self) -> None:
        self._node_parser = NodeParser()
        self._tree_parser = TreeParser()
        self._shuffle_detector = ShuffleBoundaryDetector()

    def parse(self, plan: str) -> ParsedPlan:
        tree_lines: list[str] = []
        node_lines: list[str] = []
        current = tree_lines

        for line in plan.splitlines():
            if _OPERATOR_HEADER.match(line.strip()):
                current = node_lines
            current.append(line)

        operators = self._node_parser.parse(node_lines)

        for op in operators.values():
            name = op.name
            if "BroadcastHashJoin" in name:
                op.operator_type = OperatorType.BROADCAST_HASH_JOIN
                op.transformation = TransformationType.WIDE
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
                op.operator_type = (
                    OperatorType.BROADCAST_EXCHANGE
                    if "BroadcastExchange" in name
                    else OperatorType.EXCHANGE
                )
                op.transformation = TransformationType.WIDE
            elif name == "Exchange":
                # A bare "Exchange" node (no Shuffle/Broadcast prefix) is
                # still a shuffle-boundary exchange operator -- it must not
                # fall through to UNKNOWN, or every downstream exchange/
                # shuffle/stage-counting rule silently finds nothing.
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
                op.operator_type = OperatorType.UNKNOWN
                if op.transformation == TransformationType.NONE:
                    op.transformation = TransformationType.NARROW

        edges = self._tree_parser.parse(tree_lines)

        for parent_id, child_id in edges:
            if parent_id not in operators or child_id not in operators:
                raise ValueError(
                    f"TreeParser invariant violated: edge ({parent_id}, {child_id}) "
                    f"references an id not present in NodeParser output. "
                    f"This indicates a bug in EdgeBuilder's wrapper-skipping logic."
                )

        return ParsedPlan(operators=operators, edges=edges)