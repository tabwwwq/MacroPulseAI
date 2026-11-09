"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from macropulse_api import __version__
from macropulse_api.config import Settings, get_settings
from macropulse_api.db import build_engine, build_sessionmaker
from macropulse_api.errors import install_error_handlers
from macropulse_api.logging_config import configure_logging
from macropulse_api.middleware import install_request_middleware
from macropulse_api.routers import countries, health, indicators, series, sources

DESCRIPTION = """
Macroeconomic intelligence and technical-recession early-warning API.

* **Historical statistics** come only from official sources (Eurostat, ECB, FRED, World Bank, OECD)
  with provenance; missing data is reported as missing, never imputed silently.
* **Model outputs** are analytical estimates, not investment advice. A *technical recession* (two
  consecutive negative q/q real-GDP quarters) is distinct from an official NBER recession.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(
        title="MacroPulse AI API",
        version=__version__,
        description=DESCRIPTION,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = build_sessionmaker(engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    install_request_middleware(app)
    install_error_handlers(app)

    app.include_router(health.router)
    app.include_router(countries.router)
    app.include_router(sources.router)
    app.include_router(indicators.router)
    app.include_router(series.router)
    return app
