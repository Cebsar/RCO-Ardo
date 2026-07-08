from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.common import APIResponse, ErrorDetail, ResponseMeta


class KPIResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pipeline_executions": 1,
                    "successful_executions": 1,
                    "failed_executions": 0,
                    "accounting_entries": 1,
                    "dre_nodes": 1,
                    "reconciliation_rows": 1,
                    "average_duration_seconds": 2.0,
                    "latest_execution_id": "exec-1",
                    "warnings": [],
                }
            ],
        }
    )

    pipeline_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    accounting_entries: int = 0
    dre_nodes: int = 0
    reconciliation_rows: int = 0
    average_duration_seconds: float = 0.0
    latest_execution_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    executive: dict = Field(default_factory=dict)
    charts: dict = Field(default_factory=dict)
    drilldown: dict = Field(default_factory=dict)
    pagination: dict = Field(default_factory=dict)


class KPIAPIResponse(APIResponse):
    data: KPIResponse
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)
