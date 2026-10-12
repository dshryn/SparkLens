from __future__ import annotations

import re

from models.enums import OperatorType
from models.physical_operator import PhysicalOperator

_PARTITION_COUNT = re.compile(
    r"(?:hash|range)partitioning\(.*?,\s*(\d+)\)",
    re.IGNORECASE,
)


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
