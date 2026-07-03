from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class DREDTO:
    period: str
    root_node: Any
    metadata: Optional[Mapping[str, Any]] = None
