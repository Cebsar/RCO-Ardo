from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.metadata import API_VERSION
from api.schemas.common import APIResponse, response_meta
from api.security import require_principal
from src.infrastructure.persistence.models import (
    ExecutionMetricsORM,
    FactAccountingEntryORM,
    FactDREORM,
    FactReconciliationORM,
    PipelineExecutionORM,
)

router = APIRouter(tags=["operations"], dependencies=[Depends(require_principal)])


def _latest_execution(session: Session) -> PipelineExecutionORM | None:
    stmt = select(PipelineExecutionORM).order_by(PipelineExecutionORM.created_at.desc()).limit(1)
    return session.scalar(stmt)


def _count(session: Session, model: type, execution_id: str) -> int:
    stmt = select(func.count()).select_from(model).where(model.pipeline_execution_id == execution_id)
    return int(session.scalar(stmt) or 0)


@router.get("/reconciliation", response_model=APIResponse, summary="Get latest reconciliation")
def reconciliation(session: Session = Depends(get_db_session)) -> APIResponse:
    execution = _latest_execution(session)
    rows = []
    if execution is not None:
        stmt = (
            select(FactReconciliationORM)
            .where(FactReconciliationORM.pipeline_execution_id == execution.id)
            .order_by(FactReconciliationORM.node_code.asc())
            .limit(500)
        )
        rows = [
            {
                "node_code": row.node_code,
                "node_name": row.node_name,
                "expected_amount": row.expected_amount,
                "actual_amount": row.actual_amount,
                "difference_amount": row.difference_amount,
                "status": "pass" if row.difference_amount in (None, 0) else "fail",
            }
            for row in session.scalars(stmt)
        ]
    return APIResponse(
        data={"latest_execution_id": execution.id if execution else None, "rows": rows},
        meta=response_meta(API_VERSION),
    )


@router.get("/validation", response_model=APIResponse, summary="Get latest validation")
def validation(session: Session = Depends(get_db_session)) -> APIResponse:
    execution = _latest_execution(session)
    if execution is None:
        data = {"latest_execution_id": None, "issues": [], "metrics": {}}
    else:
        metrics = {
            "accounting_entries": _count(session, FactAccountingEntryORM, execution.id),
            "dre_nodes": _count(session, FactDREORM, execution.id),
            "reconciliation_rows": _count(session, FactReconciliationORM, execution.id),
            "metrics_rows": _count(session, ExecutionMetricsORM, execution.id),
        }
        issues = [
            {"type": "error", "message": str(error)}
            for error in (execution.errors or [])
        ]
        data = {"latest_execution_id": execution.id, "issues": issues, "metrics": metrics}
    return APIResponse(data=data, meta=response_meta(API_VERSION))


@router.get("/downloads", response_model=APIResponse, summary="Get generated artifact metadata")
def downloads(session: Session = Depends(get_db_session)) -> APIResponse:
    execution = _latest_execution(session)
    artifacts = []
    if execution is not None:
        counts = {
            "FACT_ACCOUNTING_ENTRY.xlsx": _count(session, FactAccountingEntryORM, execution.id),
            "FATO_DRE.xlsx": _count(session, FactDREORM, execution.id),
            "Reconciliation_Report.xlsx": _count(session, FactReconciliationORM, execution.id),
            "Execution_Metrics.json": _count(session, ExecutionMetricsORM, execution.id),
        }
        artifacts = [
            {
                "filename": filename,
                "record_count": record_count,
                "pipeline_execution_id": execution.id,
                "source_path": execution.source_path,
            }
            for filename, record_count in counts.items()
        ]
    return APIResponse(
        data={"latest_execution_id": execution.id if execution else None, "artifacts": artifacts},
        meta=response_meta(API_VERSION),
    )
