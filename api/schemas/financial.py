from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.common import APIResponse, ErrorDetail, ResponseMeta


class DRERequest(BaseModel):
    company: str | None = Field(default=None, examples=["company-a"])
    period: str | None = Field(default=None, examples=["202606"])


class DRERow(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "node_code": "4",
                    "node_name": "Revenue",
                    "level": 1,
                    "amount": "100.00",
                    "currency": "BRL",
                    "percentage": None,
                    "parent_node_code": None,
                    "ordinal": 0,
                    "rule_id": None,
                    "payload": {"node_code": "4"},
                }
            ],
        }
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filters": {"company": "company-a", "period": "202606"},
                    "nodes": [DRERow.model_config["json_schema_extra"]["examples"][0]],
                }
            ],
        }
    )

    filters: DREFilter
    nodes: list[DRERow] = Field(default_factory=list)


class DRETreeAPIResponse(APIResponse):
    data: DRETreeResponse
    meta: ResponseMeta
    errors: list[ErrorDetail] = Field(default_factory=list)
