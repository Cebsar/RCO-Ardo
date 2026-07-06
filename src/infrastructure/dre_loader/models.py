from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities import DRENode


@dataclass(frozen=True)
class DRETree:
    roots: Tuple[DRENode, ...]
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionMetrics:
    nodes_processed: int = 0
    max_depth: int = 0
    execution_time_seconds: float = 0.0


@dataclass(frozen=True)
class TreeValidationReport:
    is_valid: bool = True
    nodes_validated: int = 0
    root_nodes: int = 0
    leaf_nodes: int = 0
    max_depth: int = 0
    warnings: Tuple[str, ...] = ()
    parent_by_code: Dict[str, Optional[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class TraversalReport:
    traversal_order: Tuple[str, ...] = ()
    nodes_visited: int = 0
    deterministic: bool = True
    parent_by_code: Dict[str, Optional[str]] = field(default_factory=dict)


@dataclass
class HierarchyReport:
    rows_read: int = 0
    nodes_count: int = 0
    root_nodes: int = 0
    max_level: int = 0
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    tree_validation: Optional[TreeValidationReport] = None
    traversal: Optional[TraversalReport] = None
    execution_metrics: Optional[ExecutionMetrics] = None

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)
