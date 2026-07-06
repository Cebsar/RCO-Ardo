from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_analytics_service
from api.schemas.analytics import KPIAPIResponse
from api.services.analytics import AnalyticsService
from api.security import require_principal

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(require_principal)])


@router.get("/kpis", response_model=KPIAPIResponse, summary="Get enterprise KPIs")
def kpis(service: AnalyticsService = Depends(get_analytics_service)) -> KPIAPIResponse:
    return service.kpis()
