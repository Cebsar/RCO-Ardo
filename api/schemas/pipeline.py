from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PipelineExecutionSummary(BaseModel):
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
    executions: list[PipelineExecutionSummary] = Field(default_factory=list)


class PipelineExecutionResponse(BaseModel):
    execution: PipelineExecutionDetail
