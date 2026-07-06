from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    code: str = Field(examples=["not_found"])
    message: str = Field(examples=["Resource not found"])
    details: dict[str, Any] = Field(default_factory=dict)


class ResponseMeta(BaseModel):
    api_version: str = Field(examples=["0.2.0"])
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class APIResponse(BaseModel):
    data: Any
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)


def response_meta(api_version: str) -> ResponseMeta:
    return ResponseMeta(api_version=api_version)
