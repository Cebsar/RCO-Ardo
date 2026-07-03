from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities import DRENode


@dataclass(frozen=True)
class DRETree:
    roots: Tuple[DRENode, ...]
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HierarchyReport:
    rows_read: int = 0
    nodes_count: int = 0
    root_nodes: int = 0
    max_level: int = 0
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)
