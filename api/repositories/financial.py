from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.persistence.models import FactDREORM, PipelineExecutionORM


class FinancialRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_dre_nodes(
        self,
        *,
        company: str | None = None,
        period: str | None = None,
        limit: int = 500,
    ) -> list[FactDREORM]:
        latest_execution_id = self._latest_execution_id(company=company, period=period)
        if latest_execution_id is None:
            return []
        stmt = (
            select(FactDREORM)
            .where(FactDREORM.pipeline_execution_id == latest_execution_id)
            .order_by(FactDREORM.level.asc(), FactDREORM.ordinal.asc(), FactDREORM.node_code.asc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def _latest_execution_id(self, *, company: str | None, period: str | None) -> str | None:
        stmt = select(PipelineExecutionORM).where(PipelineExecutionORM.success.is_(True))
        if company:
            stmt = stmt.where(PipelineExecutionORM.source_path.ilike(f"%{company}%"))
        if period:
            stmt = stmt.where(PipelineExecutionORM.source_path.ilike(f"%{period}%"))
        stmt = stmt.order_by(PipelineExecutionORM.created_at.desc()).limit(1)
        execution = self.session.scalar(stmt)
        return execution.id if execution is not None else None
