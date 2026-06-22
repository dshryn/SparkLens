from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import json
from typing import Any


@dataclass(slots=True)
class BaseModel:
    """
    Base class for all SparkLens domain models.

    Provides serialization helpers used throughout.
    """

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            default=str,
        )