from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_security_settings
from api.middleware.request_context import RequestContextMiddleware
from api.metadata import API_DESCRIPTION, API_TITLE, API_VERSION
from api.routers import analytics, auth, financial, operations, pipeline, system


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
    settings = get_security_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(auth.router)
    app.include_router(system.router)
    app.include_router(pipeline.router)
    app.include_router(financial.router)
    app.include_router(analytics.router)
    app.include_router(operations.router)
    return app


app = create_app()
