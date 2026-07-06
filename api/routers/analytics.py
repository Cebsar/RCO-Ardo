from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_analytics_service
from api.schemas.analytics import KPIResponse
from api.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/kpis", response_model=KPIResponse, summary="Get enterprise KPIs")
def kpis(service: AnalyticsService = Depends(get_analytics_service)) -> KPIResponse:
    return service.kpis()
