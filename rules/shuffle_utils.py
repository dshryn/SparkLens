from __future__ import annotations

import re

from models.enums import OperatorType
from models.physical_operator import PhysicalOperator

_PARTITION_COUNT = re.compile(
    r"(?:hash|range)partitioning\(.*?,\s*(\d+)\)",
    re.IGNORECASE,
)
_PART_KEYS = re.compile(
    r"(?:hash|range)partitioning\((.*),\s*\d+\)",
    re.IGNORECASE,
)
_SORT_SUFFIX = re.compile(
    r"\s+(?:ASC|DESC)(?:\s+NULLS\s+(?:FIRST|LAST))?\s*$",
    re.IGNORECASE,
)
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def is_shuffle_boundary(operator: PhysicalOperator) -> bool:
    """
    True for an Exchange that starts a new stage.

    Photon plans emit a ShuffleExchangeSink AND a ShuffleExchangeSource for
    ONE shuffle. Only the sink side is counted as the boundary.
    """
    if operator.operator_type != OperatorType.EXCHANGE:
        return False

    return "shuffleexchangesource" not in operator.name.lower()


def shuffle_partition_count(operator: PhysicalOperator) -> int | None:
    """Partition count from hashpartitioning(..., N) / rangepartitioning(..., N)."""
    match = _PARTITION_COUNT.search(" ".join(operator.arguments))
    return int(match.group(1)) if match else None


def clean_keys(raw: str) -> list[str]:
    """Clean and deduplicate identifier-like partition or join keys."""
    keys: list[str] = []

    for part in raw.strip("[] ").split(","):
        key = _SORT_SUFFIX.sub(
            "",
            re.sub(r"#\d+L?", "", part),
        ).strip("[] ")

        if _IDENT.match(key) and key not in keys:
            keys.append(key)

    return keys


def partitioning_keys(operator: PhysicalOperator) -> list[str]:
    match = _PART_KEYS.search(" ".join(operator.arguments))
    return clean_keys(match.group(1)) if match else []


def format_keys(keys: list[str]) -> str:
    """Format zero, one, or multiple keys for a sentence."""
    if not keys:
        return ""
    if len(keys) == 1:
        return keys[0]
    return ", ".join(keys[:-1]) + " and " + keys[-1]
