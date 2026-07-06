from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import (
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)


class AnalyticsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_kpis(self) -> dict[str, object]:
        latest_stmt = select(PipelineExecutionORM.id).order_by(PipelineExecutionORM.created_at.desc()).limit(1)
        return {
            "pipeline_executions": self._count(PipelineExecutionORM),
            "successful_executions": self._count(PipelineExecutionORM, PipelineExecutionORM.success.is_(True)),
            "failed_executions": self._count(PipelineExecutionORM, PipelineExecutionORM.success.is_(False)),
            "accounting_entries": self._count(FactAccountingEntryORM),
            "dre_nodes": self._count(FactDREORM),
            "reconciliation_rows": self._count(FactReconciliationORM),
            "average_duration_seconds": float(
                self.session.scalar(select(func.avg(PipelineExecutionORM.duration_seconds))) or 0.0
            ),
            "latest_execution_id": self.session.scalar(latest_stmt),
        }

    def _count(self, model: type, predicate=None) -> int:
        stmt = select(func.count()).select_from(model)
        if predicate is not None:
            stmt = stmt.where(predicate)
        return int(self.session.scalar(stmt) or 0)
