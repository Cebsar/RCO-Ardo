from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    database: str = Field(examples=["ok"])


class VersionResponse(BaseModel):
    name: str
    version: str
    generated_at: datetime
