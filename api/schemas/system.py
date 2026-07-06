from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.common import APIResponse, ErrorDetail, ResponseMeta


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"status": "ok", "database": "ok"}],
        }
    )

    status: str = Field(examples=["ok"])
    database: str = Field(examples=["ok"])


class VersionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "ARDO Enterprise Financial API",
                    "version": "0.2.0",
                    "generated_at": "2026-07-06T10:00:00Z",
                }
            ],
        }
    )

    name: str
    version: str
    generated_at: datetime


class HealthAPIResponse(APIResponse):
    data: HealthResponse
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)


class VersionAPIResponse(APIResponse):
    data: VersionResponse
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)
