from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class MasterFileDTO:
    path: str
    metadata: Optional[Mapping[str, Any]] = None
