from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from src.infrastructure.warehouse.models import DimensionRow, FactRow
from src.infrastructure.warehouse.store import OperationalDataStore

logger = logging.getLogger(__name__)


class WarehouseExporter:
    def __init__(self, store: OperationalDataStore):
        self.store = store

    def export_to_csv(self, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        self._export_dimension_csv(target_dir / "DIM_COMPANY.csv", self.store.companies.values())
        self._export_dimension_csv(target_dir / "DIM_DIVISION.csv", self.store.divisions.values())
        self._export_dimension_csv(target_dir / "DIM_COSTCENTER.csv", self.store.costcenters.values())
        self._export_dimension_csv(target_dir / "DIM_ACCOUNT.csv", self.store.accounts.values())
        self._export_dimension_csv(target_dir / "DIM_PERIOD.csv", self.store.periods.values())
        self._export_fact_csv(target_dir / "FACT_ACCOUNTING_ENTRY.csv", self.store.facts.values())
        logger.info("Warehouse exported to %s", target_dir)

    def export_to_json(self, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        self._export_json(target_dir / "DIM_COMPANY.json", self.store.companies.values())
        self._export_json(target_dir / "DIM_DIVISION.json", self.store.divisions.values())
        self._export_json(target_dir / "DIM_COSTCENTER.json", self.store.costcenters.values())
        self._export_json(target_dir / "DIM_ACCOUNT.json", self.store.accounts.values())
        self._export_json(target_dir / "DIM_PERIOD.json", self.store.periods.values())
        self._export_json(target_dir / "FACT_ACCOUNTING_ENTRY.json", self.store.facts.values())
        logger.info("Warehouse exported to %s", target_dir)

    def _export_dimension_csv(self, path, rows: Iterable[DimensionRow]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["surrogate_key", "natural_key", "attributes"])
            for row in rows:
                writer.writerow([row.surrogate_key, row.natural_key, json.dumps(row.attributes, ensure_ascii=False)])

    def _export_fact_csv(self, path, rows: Iterable[FactRow]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "surrogate_key",
                "entry_id",
                "company_key",
                "division_key",
                "costcenter_key",
                "account_key",
                "period_key",
                "amount",
                "entry_type",
                "accounting_date",
                "description",
                "source_row",
            ])
            for row in rows:
                writer.writerow([
                    row.surrogate_key,
                    row.entry_id,
                    row.company_key,
                    row.division_key,
                    row.costcenter_key,
                    row.account_key,
                    row.period_key,
                    str(row.amount),
                    row.entry_type,
                    row.accounting_date.isoformat(),
                    row.description,
                    json.dumps(row.source_row, ensure_ascii=False),
                ])

    def _export_json(self, path, rows):
        with path.open("w", encoding="utf-8") as handle:
            json.dump([self._row_to_dict(row) for row in rows], handle, ensure_ascii=False, indent=2)

    def _row_to_dict(self, row):
        if isinstance(row, DimensionRow):
            return {
                "surrogate_key": row.surrogate_key,
                "natural_key": row.natural_key,
                "attributes": row.attributes,
            }
        if isinstance(row, FactRow):
            return {
                "surrogate_key": row.surrogate_key,
                "entry_id": row.entry_id,
                "company_key": row.company_key,
                "division_key": row.division_key,
                "costcenter_key": row.costcenter_key,
                "account_key": row.account_key,
                "period_key": row.period_key,
                "amount": str(row.amount),
                "entry_type": row.entry_type,
                "accounting_date": row.accounting_date.isoformat(),
                "description": row.description,
                "source_row": row.source_row,
            }
