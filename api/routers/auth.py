from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.schemas.security import TokenResponse
from api.services.security import SecurityService

router = APIRouter(prefix="/auth", tags=["security"])


def get_security_service() -> SecurityService:
    return SecurityService()


@router.post("/token", response_model=TokenResponse, summary="Issue OAuth2 access token")
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: SecurityService = Depends(get_security_service),
) -> TokenResponse:
    return service.issue_token(form_data.username, form_data.password)
