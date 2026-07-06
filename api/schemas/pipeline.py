from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.common import APIResponse, ErrorDetail, ResponseMeta


class PipelineHistoryRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200, examples=[50])


class PipelineExecutionRequest(BaseModel):
    execution_id: str = Field(examples=["exec-1"])


class PipelineExecutionSummary(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "exec-1",
                    "pipeline_name": "ARDO Pipeline",
                    "source_path": "data/master/company-a-202606.xlsx",
                    "status": "succeeded",
                    "success": True,
                    "started_at": "2026-07-06T09:00:00",
                    "finished_at": "2026-07-06T09:00:02",
                    "duration_seconds": 2.0,
                    "created_at": "2026-07-06T09:00:03",
                }
            ],
        }
    )

    id: str
    pipeline_name: str
    source_path: str | None = None
    status: str
    success: bool
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float
    created_at: datetime


class PipelineExecutionDetail(PipelineExecutionSummary):
    errors: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    accounting_entries: int = 0
    dre_nodes: int = 0
    reconciliation_rows: int = 0
    metrics_rows: int = 0


class PipelineHistoryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"executions": [PipelineExecutionSummary.model_config["json_schema_extra"]["examples"][0]]}],
        }
    )

    executions: list[PipelineExecutionSummary] = Field(default_factory=list)


class PipelineExecutionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "execution": {
                        **PipelineExecutionSummary.model_config["json_schema_extra"]["examples"][0],
                        "errors": [],
                        "metadata": {"source": "integration"},
                        "accounting_entries": 1,
                        "dre_nodes": 1,
                        "reconciliation_rows": 1,
                        "metrics_rows": 1,
                    }
                }
            ],
        }
    )

    execution: PipelineExecutionDetail


class PipelineHistoryAPIResponse(APIResponse):
    data: PipelineHistoryResponse
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)


class PipelineExecutionAPIResponse(APIResponse):
    data: PipelineExecutionResponse
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)
