from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from time import perf_counter
from typing import Dict, Iterable, List, Optional

from src.domain.entities import AccountingEntry, Account, CostCenter
from src.domain.value_objects import AccountCode, CostCenterCode
from src.domain.enums import EntryType
from src.infrastructure.warehouse.models import FactRow, WarehouseReport
from src.infrastructure.warehouse.store import OperationalDataStore

logger = logging.getLogger(__name__)


class DimensionBuilder:
    def __init__(self, store: OperationalDataStore):
        self.store = store

    def build_company(self, entry: AccountingEntry) -> int:
        company = getattr(entry, "company", None)
        if company is not None:
            key = company.code.value
            attributes = {"name": company.name}
        else:
            key = entry.account.code.value
            attributes = {"name": entry.account.name, "source": "account_fallback"}
        row = self.store.ensure_dimension("companies", key, attributes)
        return row.surrogate_key

    def build_division(self, entry: AccountingEntry) -> Optional[int]:
        if entry.cost_center is None or entry.cost_center.division is None:
            return None
        key = entry.cost_center.division.code.value
        attributes = {
            "name": entry.cost_center.division.name,
            "company_key": entry.cost_center.division.company.code.value,
        }
        row = self.store.ensure_dimension("divisions", key, attributes)
        return row.surrogate_key

    def build_costcenter(self, entry: AccountingEntry) -> Optional[int]:
        if entry.cost_center is None:
            return None
        key = entry.cost_center.code.value
        attributes = {"name": entry.cost_center.name}
        if entry.cost_center.division:
            attributes["division_code"] = entry.cost_center.division.code.value
        row = self.store.ensure_dimension("costcenters", key, attributes)
        return row.surrogate_key

    def build_account(self, entry: AccountingEntry) -> int:
        key = entry.account.code.value
        attributes = {"name": entry.account.name, "type": entry.account.type.value}
        row = self.store.ensure_dimension("accounts", key, attributes)
        return row.surrogate_key

    def build_period(self, entry: AccountingEntry) -> int:
        if not hasattr(entry, "date"):
            raise ValueError("AccountingEntry must have date")
        period_key = entry.date.strftime("%Y%m")
        attributes = {"year": entry.date.year, "month": entry.date.month}
        row = self.store.ensure_dimension("periods", period_key, attributes)
        return row.surrogate_key


class FactBuilder:
    def __init__(self, store: OperationalDataStore):
        self.store = store

    def build_fact(self, entry: AccountingEntry, company_key: int, division_key: Optional[int], costcenter_key: Optional[int], account_key: int, period_key: int) -> FactRow:
        surrogate_key = self.store._get_next_key()
        return FactRow(
            surrogate_key=surrogate_key,
            entry_id=entry.id,
            company_key=company_key,
            division_key=division_key,
            costcenter_key=costcenter_key,
            account_key=account_key,
            period_key=period_key,
            amount=entry.amount if isinstance(entry.amount, Decimal) else Decimal(entry.amount.amount),
            entry_type=entry.entry_type.value,
            accounting_date=entry.date,
            description=entry.description,
            source_row={
                "account_code": entry.account.code.value,
                "company": entry.company.code.value if getattr(entry, "company", None) else None,
                "division": entry.cost_center.division.code.value if entry.cost_center and entry.cost_center.division else None,
                "cost_center": entry.cost_center.code.value if entry.cost_center else None,
                "entry_id": entry.id,
            },
            source_entry=entry,
        )


class WarehouseBuilder:
    def __init__(self, store: Optional[OperationalDataStore] = None):
        self.store = store or OperationalDataStore()
        self.dimension_builder = DimensionBuilder(self.store)
        self.fact_builder = FactBuilder(self.store)

    def build(self, entries: Iterable[AccountingEntry]) -> WarehouseReport:
        start = perf_counter()
        report = WarehouseReport()

        for entry in entries:
            company_key = self.dimension_builder.build_company(entry)
            division_key = self.dimension_builder.build_division(entry)
            costcenter_key = self.dimension_builder.build_costcenter(entry)
            account_key = self.dimension_builder.build_account(entry)
            period_key = self.dimension_builder.build_period(entry)

            fact = self.fact_builder.build_fact(entry, company_key, division_key, costcenter_key, account_key, period_key)
            existing = self.store.facts.get(entry.id)
            persisted = self.store.add_fact(fact)
            if existing is None:
                report.new_rows += 1
            else:
                report.updated_rows += 1

            report.company_rows = len(self.store.companies)
            report.division_rows = len(self.store.divisions)
            report.costcenter_rows = len(self.store.costcenters)
            report.account_rows = len(self.store.accounts)
            report.period_rows = len(self.store.periods)
            report.fact_rows = len(self.store.facts)

        report.execution_time_seconds = perf_counter() - start
        logger.info("Warehouse build completed in %.6f seconds: %d facts", report.execution_time_seconds, report.fact_rows)
        return report
