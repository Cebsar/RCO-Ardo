from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class DRERow(BaseModel):
    node_code: str
    node_name: str
    level: int
    amount: Decimal | None = None
    currency: str
    percentage: Decimal | None = None
    parent_node_code: str | None = None
    ordinal: int
    rule_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class DREFilter(BaseModel):
    company: str | None = None
    period: str | None = None


class DRETreeResponse(BaseModel):
    filters: DREFilter
    nodes: list[DRERow] = Field(default_factory=list)
