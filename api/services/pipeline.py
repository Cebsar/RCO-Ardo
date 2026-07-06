from __future__ import annotations

from fastapi import HTTPException, status

from api.repositories.pipeline import PipelineRepository
from api.schemas.pipeline import (
    PipelineExecutionDetail,
    PipelineExecutionResponse,
    PipelineExecutionSummary,
    PipelineHistoryResponse,
)


class PipelineService:
    def __init__(self, repository: PipelineRepository):
        self.repository = repository

    def history(self, limit: int = 50) -> PipelineHistoryResponse:
        executions = [self._summary(row) for row in self.repository.list_history(limit=limit)]
        return PipelineHistoryResponse(executions=executions)

    def get_execution(self, execution_id: str) -> PipelineExecutionResponse:
        execution = self.repository.get(execution_id)
        if execution is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline execution not found")
        detail = PipelineExecutionDetail(
            **self._summary(execution).model_dump(),
            errors=execution.errors,
            metadata=execution.execution_metadata,
            accounting_entries=self.repository.count_accounting_entries(execution.id),
            dre_nodes=self.repository.count_dre_nodes(execution.id),
            reconciliation_rows=self.repository.count_reconciliation_rows(execution.id),
            metrics_rows=self.repository.count_metrics(execution.id),
        )
        return PipelineExecutionResponse(execution=detail)

    def _summary(self, row) -> PipelineExecutionSummary:
        return PipelineExecutionSummary(
            id=row.id,
            pipeline_name=row.pipeline_name,
            source_path=row.source_path,
            status=row.status,
            success=row.success,
            started_at=row.started_at,
            finished_at=row.finished_at,
            duration_seconds=row.duration_seconds,
            created_at=row.created_at,
        )
