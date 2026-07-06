from __future__ import annotations

from api.metadata import API_VERSION
from api.repositories.analytics import AnalyticsRepository
from api.schemas.analytics import KPIAPIResponse, KPIResponse
from api.schemas.common import response_meta


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def kpis(self) -> KPIAPIResponse:
        return KPIAPIResponse(data=KPIResponse(**self.repository.get_kpis()), meta=response_meta(API_VERSION))
