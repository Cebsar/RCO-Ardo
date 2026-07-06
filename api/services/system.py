from __future__ import annotations

from datetime import UTC, datetime

from api.metadata import API_TITLE, API_VERSION
from api.repositories.system import SystemRepository
from api.schemas.system import HealthResponse, VersionResponse


class SystemService:
    def __init__(self, repository: SystemRepository):
        self.repository = repository

    def health(self) -> HealthResponse:
        return HealthResponse(status="ok", database="ok" if self.repository.ping() else "unavailable")

    def version(self) -> VersionResponse:
        return VersionResponse(name=API_TITLE, version=API_VERSION, generated_at=datetime.now(UTC))
