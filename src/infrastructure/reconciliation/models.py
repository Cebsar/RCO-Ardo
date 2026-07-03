from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.entities import DRENode


@dataclass(frozen=True)
class ToleranceRule:
    absolute: Decimal = Decimal("0")
    relative: Decimal = Decimal("0")

    def evaluate(self, expected: Decimal, actual: Decimal) -> bool:
        if expected == Decimal("0"):
            return actual == Decimal("0") if self.absolute == Decimal("0") else abs(actual) <= self.absolute
        delta = abs(actual - expected)
        return delta <= self.absolute or delta <= abs(expected) * self.relative


@dataclass(frozen=True)
class DifferenceItem:
    node_code: str
    node_name: str
    expected: Optional[Decimal]
    actual: Optional[Decimal]
    difference: Optional[Decimal]
    tolerance: ToleranceRule
    percentage_difference: Optional[Decimal] = None
    exists_in_expected: bool = True
    exists_in_actual: bool = True
    order_match: bool = True
    level_match: bool = True


@dataclass
class DifferenceReport:
    differences: List[DifferenceItem] = field(default_factory=list)
    mismatches: int = 0
    missing_in_expected: int = 0
    missing_in_actual: int = 0
    out_of_tolerance: int = 0
    execution_metrics: Optional["ExecutionMetrics"] = None

    def add(self, item: DifferenceItem) -> None:
        self.differences.append(item)
        if not item.exists_in_expected:
            self.missing_in_expected += 1
            self.mismatches += 1
        if not item.exists_in_actual:
            self.missing_in_actual += 1
            self.mismatches += 1
        if item.difference is not None:
            expected_value = item.expected or Decimal("0")
            actual_value = item.actual or Decimal("0")
            if not item.tolerance.evaluate(expected_value, actual_value):
                self.out_of_tolerance += 1
            if item.exists_in_expected and item.exists_in_actual and item.difference != Decimal("0"):
                self.mismatches += 1


@dataclass
class ValidationMetrics:
    nodes_compared: int = 0
    discrepancies_found: int = 0
    tolerance_checks: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class ExecutionMetrics:
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0


@dataclass
class AuditReport:
    reconciliation: DifferenceReport
    validation: ValidationMetrics
    execution: ExecutionMetrics
    source: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
