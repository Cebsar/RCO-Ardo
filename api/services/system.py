from __future__ import annotations

from datetime import UTC, datetime

from api.metadata import API_TITLE, API_VERSION
from api.repositories.system import SystemRepository
from api.schemas.common import response_meta
from api.schemas.system import HealthAPIResponse, HealthResponse, VersionAPIResponse, VersionResponse


class SystemService:
    def __init__(self, repository: SystemRepository):
        self.repository = repository

    def health(self) -> HealthAPIResponse:
        data = HealthResponse(status="ok", database="ok" if self.repository.ping() else "unavailable")
        return HealthAPIResponse(data=data, meta=response_meta(API_VERSION))

    def version(self) -> VersionAPIResponse:
        data = VersionResponse(name=API_TITLE, version=API_VERSION, generated_at=datetime.now(UTC))
        return VersionAPIResponse(data=data, meta=response_meta(API_VERSION))
