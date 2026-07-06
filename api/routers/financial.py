from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_financial_service
from api.schemas.financial import DRERequest, DRETreeAPIResponse
from api.services.financial import FinancialService
from api.security import require_principal

router = APIRouter(prefix="/financial", tags=["financial"], dependencies=[Depends(require_principal)])


@router.get("/dre", response_model=DRETreeAPIResponse, summary="Get latest DRE")
def dre(service: FinancialService = Depends(get_financial_service)) -> DRETreeAPIResponse:
    return service.dre()


@router.get("/dre/{company}", response_model=DRETreeAPIResponse, summary="Get latest company DRE")
def dre_by_company(
    company: str,
    service: FinancialService = Depends(get_financial_service),
) -> DRETreeAPIResponse:
    request = DRERequest(company=company)
    return service.dre(company=request.company)


@router.get("/dre/{company}/{period}", response_model=DRETreeAPIResponse, summary="Get company period DRE")
def dre_by_company_period(
    company: str,
    period: str,
    service: FinancialService = Depends(get_financial_service),
) -> DRETreeAPIResponse:
    request = DRERequest(company=company, period=period)
    return service.dre(company=request.company, period=request.period)
