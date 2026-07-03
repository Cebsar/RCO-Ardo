from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class WarehouseSnapshotDTO:
    source: str
    path: str
    metadata: Optional[Mapping[str, Any]] = None
