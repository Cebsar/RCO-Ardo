from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_pipeline_service
from api.schemas.pipeline import (
    PipelineExecutionAPIResponse,
    PipelineExecutionRequest,
    PipelineHistoryAPIResponse,
    PipelineHistoryRequest,
)
from api.services.pipeline import PipelineService
from api.security import require_principal

router = APIRouter(prefix="/pipeline", tags=["pipeline"], dependencies=[Depends(require_principal)])


@router.get("/history", response_model=PipelineHistoryAPIResponse, summary="List pipeline executions")
def history(
    limit: int = Query(default=50, ge=1, le=200),
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineHistoryAPIResponse:
    request = PipelineHistoryRequest(limit=limit)
    return service.history(limit=request.limit)


@router.get("/{execution_id}", response_model=PipelineExecutionAPIResponse, summary="Get pipeline execution")
def get_execution(
    execution_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineExecutionAPIResponse:
    request = PipelineExecutionRequest(execution_id=execution_id)
    return service.get_execution(request.execution_id)
