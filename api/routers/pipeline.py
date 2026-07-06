from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_pipeline_service
from api.schemas.pipeline import PipelineExecutionResponse, PipelineHistoryResponse
from api.services.pipeline import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/history", response_model=PipelineHistoryResponse, summary="List pipeline executions")
def history(
    limit: int = Query(default=50, ge=1, le=200),
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineHistoryResponse:
    return service.history(limit=limit)


@router.get("/{execution_id}", response_model=PipelineExecutionResponse, summary="Get pipeline execution")
def get_execution(
    execution_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> PipelineExecutionResponse:
    return service.get_execution(execution_id)
