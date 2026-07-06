from __future__ import annotations

from api.repositories.financial import FinancialRepository
from api.schemas.financial import DREFilter, DRERow, DRETreeResponse


class FinancialService:
    def __init__(self, repository: FinancialRepository):
        self.repository = repository

    def dre(self, *, company: str | None = None, period: str | None = None) -> DRETreeResponse:
        nodes = [
            DRERow(
                node_code=row.node_code,
                node_name=row.node_name,
                level=row.level,
                amount=row.amount,
                currency=row.currency,
                percentage=row.percentage,
                parent_node_code=row.parent_node_code,
                ordinal=row.ordinal,
                rule_id=row.rule_id,
                payload=row.payload,
            )
            for row in self.repository.list_dre_nodes(company=company, period=period)
        ]
        return DRETreeResponse(filters=DREFilter(company=company, period=period), nodes=nodes)
