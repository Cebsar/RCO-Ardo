from __future__ import annotations

from api.repositories.analytics import AnalyticsRepository
from api.schemas.analytics import KPIResponse


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def kpis(self) -> KPIResponse:
        return KPIResponse(**self.repository.get_kpis())
