from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GoldenWorkbook:
    path: Path
    fingerprint: str
    row_count: int
    columns: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GoldenOverview:
    source: str
    generated_at: datetime
    entries: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GoldenFactAccounting:
    source: str
    generated_at: datetime
    records: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GoldenDRE:
    source: str
    generated_at: datetime
    nodes: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
