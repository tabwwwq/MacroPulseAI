"""Liveness (`/api/health`) and readiness (`/api/ready`) probes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from macropulse_api import __version__
from macropulse_api.deps import SettingsDep
from macropulse_api.migrate import current_revision, head_revision
from macropulse_api.models import Country
from macropulse_api.schemas import HealthResponse, ReadinessCheck, ReadyResponse
from macropulse_economics import COUNTRIES

router = APIRouter(prefix="/api", tags=["health"])

UPGRADE_HINT = "Run `uv run macropulse db upgrade` (or `pnpm db:upgrade`)."


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health(settings: SettingsDep) -> HealthResponse:
    """Process is up. Does not touch the database or external sources."""
    return HealthResponse(
        status="ok",
        service="macropulse-api",
        version=__version__,
        environment=settings.app_env,
        time_utc=datetime.now(UTC),
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness probe",
    responses={503: {"model": ReadyResponse, "description": "One or more checks failed."}},
)
def ready(request: Request) -> JSONResponse:
    """Database reachable, schema at the latest migration and registry seeded."""
    engine = request.app.state.engine
    checks: list[ReadinessCheck] = []

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks.append(ReadinessCheck(name="database", ok=True, detail=engine.dialect.name))
        db_ok = True
    except SQLAlchemyError as exc:
        checks.append(
            ReadinessCheck(name="database", ok=False, detail=f"Unreachable ({type(exc).__name__}).")
        )
        db_ok = False

    if db_ok:
        current, head = current_revision(engine), head_revision()
        schema_ok = current is not None and current == head
        checks.append(
            ReadinessCheck(
                name="schema",
                ok=schema_ok,
                detail=f"revision {current} (head {head})"
                if schema_ok
                else f"revision {current}, expected {head}. {UPGRADE_HINT}",
            )
        )
        if schema_ok:
            with request.app.state.sessionmaker() as session:
                n = session.scalar(select(func.count()).select_from(Country)) or 0
            seeded = n == len(COUNTRIES)
            checks.append(
                ReadinessCheck(
                    name="registry",
                    ok=seeded,
                    detail=f"{n} countries registered"
                    if seeded
                    else f"{n}/{len(COUNTRIES)} countries registered. {UPGRADE_HINT}",
                )
            )

    all_ok = all(c.ok for c in checks)
    body = ReadyResponse(status="ready" if all_ok else "not_ready", checks=checks)
    return JSONResponse(status_code=200 if all_ok else 503, content=body.model_dump(mode="json"))
