from __future__ import annotations

from api.metadata import API_VERSION
from api.repositories.financial import FinancialRepository
from api.schemas.common import response_meta
from api.schemas.financial import DREFilter, DRERow, DRETreeAPIResponse, DRETreeResponse


class FinancialService:
    def __init__(self, repository: FinancialRepository):
        self.repository = repository

    def dre(self, *, company: str | None = None, period: str | None = None) -> DRETreeAPIResponse:
        persisted_nodes = self.repository.list_dre_nodes(company=company, period=period)
        rel_razao_amounts = self.repository.rel_razao_amounts(persisted_nodes, company=company, period=period)
        nodes = [
            DRERow(
                node_code=row.node_code,
                node_name=row.node_name,
                level=row.level,
                amount=rel_razao_amounts.get(row.node_code, 0),
                currency=row.currency,
                percentage=row.percentage,
                parent_node_code=row.parent_node_code,
                ordinal=row.ordinal,
                rule_id=row.rule_id,
                payload=row.payload,
            )
            for row in persisted_nodes
        ]
        return DRETreeAPIResponse(
            data=DRETreeResponse(filters=DREFilter(company=company, period=period), nodes=nodes),
            meta=response_meta(API_VERSION),
        )
