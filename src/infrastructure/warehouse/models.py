from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from src.domain.entities import AccountingEntry


@dataclass(frozen=True)
class DimensionRow:
    surrogate_key: int
    natural_key: str
    attributes: Dict[str, Any]


@dataclass(frozen=True)
class FactRow:
    surrogate_key: int
    entry_id: str
    company_key: int
    division_key: Optional[int]
    costcenter_key: Optional[int]
    account_key: int
    period_key: int
    amount: Decimal
    entry_type: str
    accounting_date: date
    description: Optional[str]
    source_row: Dict[str, Any]
    source_entry: AccountingEntry


@dataclass
class WarehouseReport:
    company_rows: int = 0
    division_rows: int = 0
    costcenter_rows: int = 0
    account_rows: int = 0
    period_rows: int = 0
    fact_rows: int = 0
    new_rows: int = 0
    updated_rows: int = 0
    execution_time_seconds: float = 0.0
