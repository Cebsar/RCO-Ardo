from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

from src.infrastructure.rule_engine.models import ExecutionReport

from .models import BusinessRuleReportEntry


@dataclass
class BusinessRuleReport:
    entries: List[BusinessRuleReportEntry]

    def add_entry(self, entry: BusinessRuleReportEntry) -> None:
        self.entries.append(entry)

    def to_dict(self) -> List[dict]:
        return [
            {
                "node_code": entry.node_code,
                "node_description": entry.node_description,
                "rule_id": entry.rule_id,
                "rule_description": entry.rule_description,
                "matched_fact_count": entry.matched_fact_count,
                "computed_value": str(entry.computed_value),
                "errors": entry.errors,
            }
            for entry in self.entries
        ]

    @classmethod
    def from_execution_report(cls, execution_report: ExecutionReport, node_names: Dict[str, str] | None = None) -> "BusinessRuleReport":
        node_names = node_names or {}
        entries: List[BusinessRuleReportEntry] = []
        for result in execution_report.results:
            entries.append(
                BusinessRuleReportEntry(
                    node_code=result.node_code,
                    node_description=node_names.get(result.node_code, ""),
                    rule_id=result.rule_id or "",
                    rule_description=result.rule_description or "",
                    matched_fact_count=result.matched_fact_count,
                    computed_value=result.value or Decimal("0"),
                    errors=result.errors,
                )
            )
        return cls(entries=entries)
