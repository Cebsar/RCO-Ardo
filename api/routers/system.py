from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_system_service
from api.schemas.system import HealthResponse, VersionResponse
from api.services.system import SystemService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health(service: SystemService = Depends(get_system_service)) -> HealthResponse:
    return service.health()


@router.get("/version", response_model=VersionResponse, summary="API version")
def version(service: SystemService = Depends(get_system_service)) -> VersionResponse:
    return service.version()
