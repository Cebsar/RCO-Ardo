from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.infrastructure.rule_engine.models import BusinessRule


@dataclass(frozen=True)
class BusinessRuleDefinition:
    id: str
    node_code: str
    description: str
    filters: Dict[str, Any]
    expression: str
    derived: bool = False
    calculated: bool = False
    children: Optional[List[str]] = None

    def to_business_rule(self) -> BusinessRule:
        return BusinessRule(
            id=self.id,
            node_code=self.node_code,
            expression=self.expression,
            description=self.description,
            filters=self.filters,
            derived=self.derived,
            calculated=self.calculated,
            children=self.children,
        )


@dataclass
class BusinessRuleReportEntry:
    node_code: str
    node_description: str
    rule_id: str
    rule_description: str
    matched_fact_count: int = 0
    computed_value: Decimal = Decimal("0")
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
