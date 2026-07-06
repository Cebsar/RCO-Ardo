from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import (
    ExecutionMetricsORM,
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)


class PipelineRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_history(self, limit: int = 50) -> list[PipelineExecutionORM]:
        stmt = (
            select(PipelineExecutionORM)
            .order_by(PipelineExecutionORM.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def get(self, execution_id: str) -> PipelineExecutionORM | None:
        return self.session.get(PipelineExecutionORM, execution_id)

    def count_accounting_entries(self, execution_id: str) -> int:
        return self._count(FactAccountingEntryORM, execution_id)

    def count_dre_nodes(self, execution_id: str) -> int:
        return self._count(FactDREORM, execution_id)

    def count_reconciliation_rows(self, execution_id: str) -> int:
        return self._count(FactReconciliationORM, execution_id)

    def count_metrics(self, execution_id: str) -> int:
        return self._count(ExecutionMetricsORM, execution_id)

    def _count(self, model: type, execution_id: str) -> int:
        stmt = select(func.count()).select_from(model).where(model.pipeline_execution_id == execution_id)
        return int(self.session.scalar(stmt) or 0)
