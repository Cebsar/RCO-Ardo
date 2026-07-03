from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.entities import DRENode


@dataclass(frozen=True)
class BusinessRule:
    id: str
    expression: str
    node_code: str = ""
    description: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    derived: bool = False
    calculated: bool = False
    subtotal: bool = False
    grand_total: bool = False
    children: Optional[List[str]] = None


@dataclass
class RuleContext:
    dre_node: DRENode
    facts: List[Dict[str, Any]]
    parameters: Dict[str, Any] = field(default_factory=dict)
    children_values: List[Decimal] = field(default_factory=list)


@dataclass
class RuleResult:
    node_code: str
    rule_id: Optional[str] = None
    rule_description: Optional[str] = None
    value: Optional[Decimal] = None
    matched_fact_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExecutionMetrics:
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    nodes_processed: int = 0
    rules_executed: int = 0


@dataclass
class ExecutionReport:
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    results: List[RuleResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CalculatedDRE:
    roots: List[DRENode]
    report: ExecutionReport
