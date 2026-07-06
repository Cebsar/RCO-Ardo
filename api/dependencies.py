from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from api.repositories.analytics import AnalyticsRepository
from api.repositories.financial import FinancialRepository
from api.repositories.pipeline import PipelineRepository
from api.repositories.system import SystemRepository
from api.services.analytics import AnalyticsService
from api.services.financial import FinancialService
from api.services.pipeline import PipelineService
from api.services.system import SystemService
from src.infrastructure.persistence.database import DatabaseConfig, create_engine_from_config, create_session_factory


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    engine = create_engine_from_config(DatabaseConfig.from_env())
    return create_session_factory(engine)


def get_db_session() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_system_service(session: Session = Depends(get_db_session)) -> SystemService:
    return SystemService(SystemRepository(session))


def get_pipeline_service(session: Session = Depends(get_db_session)) -> PipelineService:
    return PipelineService(PipelineRepository(session))


def get_financial_service(session: Session = Depends(get_db_session)) -> FinancialService:
    return FinancialService(FinancialRepository(session))


def get_analytics_service(session: Session = Depends(get_db_session)) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(session))
