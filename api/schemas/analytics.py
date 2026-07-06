from __future__ import annotations

from pydantic import BaseModel, Field


class KPIResponse(BaseModel):
    pipeline_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    accounting_entries: int = 0
    dre_nodes: int = 0
    reconciliation_rows: int = 0
    average_duration_seconds: float = 0.0
    latest_execution_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
