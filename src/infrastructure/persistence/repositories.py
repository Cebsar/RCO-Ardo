from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    ExecutionMetricsORM,
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)
from .serializers import account_code, decimal_or_none, enum_value, flatten_dre_nodes, json_safe


class PipelineExecutionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_from_report(self, report: Any, pipeline_name: str = "ARDO Pipeline") -> PipelineExecutionORM:
        config = getattr(report, "configuration", None)
        execution = PipelineExecutionORM(
            pipeline_name=pipeline_name,
            source_path=str(getattr(config, "source_path", "")) if config is not None else None,
            status="succeeded" if getattr(report, "success", False) else "failed",
            success=bool(getattr(report, "success", False)),
            started_at=getattr(report, "started_at", None),
            finished_at=getattr(report, "finished_at", None),
            duration_seconds=float(getattr(report, "duration_seconds", 0.0) or 0.0),
            errors=json_safe(getattr(report, "errors", [])),
            execution_metadata=json_safe(getattr(report, "metadata", {})),
        )
        self.session.add(execution)
        self.session.flush()
        return execution

    def get(self, execution_id: str) -> Optional[PipelineExecutionORM]:
        return self.session.get(PipelineExecutionORM, execution_id)

    def list(self) -> list[PipelineExecutionORM]:
        return list(self.session.scalars(select(PipelineExecutionORM).order_by(PipelineExecutionORM.created_at.desc())))


class AccountingEntryRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_entries(self, entries: Iterable[Any], pipeline_execution_id: str | None = None) -> list[FactAccountingEntryORM]:
        rows: list[FactAccountingEntryORM] = []
        for entry in entries:
            amount = getattr(entry, "amount", None)
            gx = dict(getattr(entry, "source_fields", {}) or {})
            row = FactAccountingEntryORM(
                pipeline_execution_id=pipeline_execution_id,
                entry_id=str(entry.id),
                period_code=entry.date.strftime("%Y%m") if getattr(entry, "date", None) else None,
                account_code=account_code(entry),
                account_name=getattr(entry.account, "name", None),
                amount=decimal_or_none(amount),
                currency=getattr(amount, "currency", "BRL"),
                entry_type=enum_value(entry.entry_type),
                accounting_date=entry.date,
                description=getattr(entry, "description", None),
                **self._gx_columns(gx),
                source_row=json_safe(entry),
            )
            self.session.add(row)
            rows.append(row)
        self.session.flush()
        return rows

    def add_fact_rows(self, facts: Iterable[Any], pipeline_execution_id: str | None = None) -> list[FactAccountingEntryORM]:
        rows: list[FactAccountingEntryORM] = []
        for fact in facts:
            entry = getattr(fact, "source_entry", None)
            gx = dict(getattr(entry, "source_fields", {}) or {}) if entry is not None else {}
            row = FactAccountingEntryORM(
                pipeline_execution_id=pipeline_execution_id,
                entry_id=str(fact.entry_id),
                company_key=getattr(fact, "company_key", None),
                division_key=getattr(fact, "division_key", None),
                costcenter_key=getattr(fact, "costcenter_key", None),
                account_key=getattr(fact, "account_key", None),
                period_key=getattr(fact, "period_key", None),
                period_code=fact.accounting_date.strftime("%Y%m") if getattr(fact, "accounting_date", None) else None,
                account_code=account_code(entry) if entry is not None else str(getattr(fact, "account_key", "")),
                account_name=getattr(getattr(entry, "account", None), "name", None),
                amount=decimal_or_none(getattr(fact, "amount", None)),
                currency=getattr(getattr(entry, "amount", None), "currency", "BRL"),
                entry_type=str(getattr(fact, "entry_type", "")),
                accounting_date=fact.accounting_date,
                description=getattr(fact, "description", None),
                **self._gx_columns(gx),
                source_row=json_safe(getattr(fact, "source_row", {})),
            )
            self.session.add(row)
            rows.append(row)
        self.session.flush()
        return rows

    @staticmethod
    def _gx_columns(gx: dict[str, Any]) -> dict[str, Any]:
        def text(key: str) -> str | None:
            value = gx.get(key)
            return None if value in (None, "") else str(value).strip()

        def integer(key: str) -> int | None:
            value = gx.get(key)
            try:
                return int(value) if value not in (None, "") else None
            except (TypeError, ValueError):
                return None

        def number(key: str):
            value = gx.get(key)
            if value in (None, "", "-"):
                return None
            try:
                return decimal_or_none(value)
            except Exception:
                return None

        return {
            "source_company": text("company"),
            "group_name": text("group"),
            "division_name": text("division"),
            "dre_group": text("dre_group"),
            "cost_center_name": text("cost_center"),
            "source_month": integer("month"),
            "source_year": integer("year"),
            "batch_number": text("batch_number"),
            "posting_number": text("posting_number"),
            "document_title": text("title"),
            "history": text("history"),
            "counterparty": text("counterparty"),
            "debit_amount": number("debit"),
            "credit_amount": number("credit"),
            "source_value": number("value"),
        }

    def list_by_execution(self, pipeline_execution_id: str) -> list[FactAccountingEntryORM]:
        stmt = select(FactAccountingEntryORM).where(FactAccountingEntryORM.pipeline_execution_id == pipeline_execution_id)
        return list(self.session.scalars(stmt))


class DRERepository:
    def __init__(self, session: Session):
        self.session = session

    def add_tree(self, roots: Iterable[Any], pipeline_execution_id: str | None = None) -> list[FactDREORM]:
        rows: list[FactDREORM] = []
        for node in flatten_dre_nodes(roots):
            row = FactDREORM(pipeline_execution_id=pipeline_execution_id, **node)
            self.session.add(row)
            rows.append(row)
        self.session.flush()
        return rows

    def list_by_execution(self, pipeline_execution_id: str) -> list[FactDREORM]:
        stmt = select(FactDREORM).where(FactDREORM.pipeline_execution_id == pipeline_execution_id).order_by(FactDREORM.ordinal)
        return list(self.session.scalars(stmt))


class ReconciliationRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_report(self, report: Any, pipeline_execution_id: str | None = None) -> list[FactReconciliationORM]:
        difference_report = getattr(report, "reconciliation", report)
        rows: list[FactReconciliationORM] = []
        for item in getattr(difference_report, "differences", []):
            tolerance = getattr(item, "tolerance", None)
            row = FactReconciliationORM(
                pipeline_execution_id=pipeline_execution_id,
                node_code=str(item.node_code),
                node_name=str(item.node_name),
                expected_amount=decimal_or_none(getattr(item, "expected", None)),
                actual_amount=decimal_or_none(getattr(item, "actual", None)),
                difference_amount=decimal_or_none(getattr(item, "difference", None)),
                tolerance_absolute=decimal_or_none(getattr(tolerance, "absolute", None)),
                tolerance_relative=decimal_or_none(getattr(tolerance, "relative", None)),
                percentage_difference=decimal_or_none(getattr(item, "percentage_difference", None)),
                exists_in_expected=bool(getattr(item, "exists_in_expected", True)),
                exists_in_actual=bool(getattr(item, "exists_in_actual", True)),
                order_match=bool(getattr(item, "order_match", True)),
                level_match=bool(getattr(item, "level_match", True)),
                payload=json_safe(item),
            )
            self.session.add(row)
            rows.append(row)
        self.session.flush()
        return rows


class ExecutionMetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_metrics(self, metrics: Any, scope: str, pipeline_execution_id: str | None = None) -> ExecutionMetricsORM:
        row = ExecutionMetricsORM(
            pipeline_execution_id=pipeline_execution_id,
            scope=scope,
            started_at=getattr(metrics, "start_time", None),
            finished_at=getattr(metrics, "end_time", None),
            duration_seconds=float(getattr(metrics, "duration_seconds", 0.0) or 0.0),
            nodes_processed=getattr(metrics, "nodes_processed", None),
            rules_executed=getattr(metrics, "rules_executed", None),
            payload=json_safe(metrics),
        )
        self.session.add(row)
        self.session.flush()
        return row


@dataclass
class UnitOfWork(AbstractContextManager["UnitOfWork"]):
    session_factory: Callable[[], Session]

    def __enter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        self.pipeline_executions = PipelineExecutionRepository(self.session)
        self.accounting_entries = AccountingEntryRepository(self.session)
        self.dre = DRERepository(self.session)
        self.reconciliation = ReconciliationRepository(self.session)
        self.metrics = ExecutionMetricsRepository(self.session)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()
