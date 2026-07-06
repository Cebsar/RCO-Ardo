from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_financial_service
from api.schemas.financial import DRETreeResponse
from api.services.financial import FinancialService

router = APIRouter(prefix="/financial", tags=["financial"])


@router.get("/dre", response_model=DRETreeResponse, summary="Get latest DRE")
def dre(service: FinancialService = Depends(get_financial_service)) -> DRETreeResponse:
    return service.dre()


@router.get("/dre/{company}", response_model=DRETreeResponse, summary="Get latest company DRE")
def dre_by_company(
    company: str,
    service: FinancialService = Depends(get_financial_service),
) -> DRETreeResponse:
    return service.dre(company=company)


@router.get("/dre/{company}/{period}", response_model=DRETreeResponse, summary="Get company period DRE")
def dre_by_company_period(
    company: str,
    period: str,
    service: FinancialService = Depends(get_financial_service),
) -> DRETreeResponse:
    return service.dre(company=company, period=period)
