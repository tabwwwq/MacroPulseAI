"""Official data-source registry with sync health derived from recorded ingestion runs."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import select

from macropulse_api.deps import SessionDep, SettingsDep
from macropulse_api.models import DataSource
from macropulse_api.schemas import SourceStatusList
from macropulse_api.services.coverage import source_status
from macropulse_economics import SOURCES

router = APIRouter(prefix="/api/sources", tags=["sources"])
_ORDER = {s.id: i for i, s in enumerate(SOURCES)}


@router.get("/status", response_model=SourceStatusList, summary="Source health and freshness")
def sources_status(session: SessionDep, settings: SettingsDep) -> SourceStatusList:
    rows = sorted(session.scalars(select(DataSource)).all(), key=lambda s: _ORDER.get(s.id, 99))
    configured = {"FRED_API_KEY": settings.fred_api_key is not None}
    items = [
        source_status(session, row, configured.get(row.api_key_env or "", False)) for row in rows
    ]
    return SourceStatusList(items=items, generated_at=datetime.now(UTC))
