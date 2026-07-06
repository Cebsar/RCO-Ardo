from __future__ import annotations

from fastapi import FastAPI

from api.middleware.request_context import RequestContextMiddleware
from api.metadata import API_DESCRIPTION, API_TITLE, API_VERSION
from api.routers import analytics, financial, pipeline, system


def create_app() -> FastAPI:
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        contact={"name": "ARDO Financial Analytics"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(system.router)
    app.include_router(pipeline.router)
    app.include_router(financial.router)
    app.include_router(analytics.router)
    return app


app = create_app()
