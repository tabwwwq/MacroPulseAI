"""Data lineage and quality: per-series inventory and raw-observation CSV export."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Query, Response

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.routers.countries import Iso2, unsupported_country
from macropulse_api.schemas import DataQualityReport, ErrorResponse
from macropulse_api.services.coverage import SYNC_HINT
from macropulse_api.services.quality_report import (
    expected_series,
    observations_csv,
    quality_report,
)
from macropulse_economics import get_country

router = APIRouter(tags=["data quality"])


@router.get(
    "/api/data-quality",
    response_model=DataQualityReport,
    summary="Lineage and latest quality checks of every mapped native series",
)
def all_data_quality(session: SessionDep) -> DataQualityReport:
    return quality_report(session)


@router.get(
    "/api/countries/{iso2}/data-quality",
    response_model=DataQualityReport,
    summary="Lineage and latest quality checks of the series behind one country",
    responses={422: {"model": ErrorResponse, "description": "Unsupported country."}},
)
def country_data_quality(session: SessionDep, iso2: Iso2) -> DataQualityReport:
    if get_country(iso2) is None:
        raise unsupported_country(iso2)
    return quality_report(session, iso2.upper())


@router.get(
    "/api/observations/export",
    summary="Raw stored observations of one native series as CSV, with per-row provenance",
    response_class=Response,
    responses={
        200: {"content": {"text/csv": {}}, "description": "RFC 4180 CSV."},
        404: {"model": ErrorResponse, "description": "Unknown series id."},
        503: {"model": ErrorResponse, "description": "Series not synced yet."},
    },
)
def export_observations(
    session: SessionDep,
    series_id: Annotated[
        str, Query(min_length=5, max_length=200, description="Native series id (see data-quality).")
    ],
) -> Response:
    if series_id not in expected_series():
        raise ApiError(404, "series_not_found", "Unknown series id; see /api/data-quality.")
    text, rows = observations_csv(session, series_id)
    if rows == 0:
        raise ApiError(
            503, "data_not_synced", f"No observations stored for {series_id}. {SYNC_HINT}"
        )
    filename = "macropulse_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", series_id).strip("_")[:120] + ".csv"
    return Response(
        content=text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
