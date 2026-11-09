"""`GET /api/indicators`: stored official series for one country and indicator, with derivation,
provenance and the quality checks of the latest ingestion attempt."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import ErrorResponse, IndicatorSeries, SeriesPoint
from macropulse_api.services.series_data import (
    indicator_definition,
    latest_checks,
    load_indicator,
    provenance,
    resolve_indicator,
)
from macropulse_economics import get_country
from macropulse_economics.periods import period_start, shift

router = APIRouter(prefix="/api/indicators", tags=["indicators"])

MAX_POINTS = 5000
PeriodQuery = Annotated[
    str | None,
    Query(
        pattern=r"^\d{4}(-Q[1-4]|-\d{2}(-\d{2})?)?$",
        description="Period bound: YYYY, YYYY-Qn, YYYY-MM or YYYY-MM-DD.",
    ),
]
IndicatorQuery = Annotated[str, Query(pattern=r"^[a-z_]{2,40}$", description="Indicator id.")]
CountryQuery = Annotated[str, Query(pattern=r"^[A-Za-z]{2}$", description="ISO alpha-2 code.")]


def period_bound(label: str | None, *, end: bool) -> date | None:
    """Inclusive date bound for a period label (end bounds cover the whole period)."""
    if label is None:
        return None
    if len(label) == 4:
        return date(int(label), 12, 31) if end else date(int(label), 1, 1)
    start = period_start(label)
    if not end or len(label) == 10:
        return start
    return period_start(shift(label, 1)) - timedelta(days=1)


@router.get(
    "",
    response_model=IndicatorSeries,
    summary="Observed (or transparently derived) series for one country and indicator",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not published / not mapped for this country.",
        },
        422: {"model": ErrorResponse, "description": "Unsupported country, indicator or bounds."},
        503: {"model": ErrorResponse, "description": "Mapped but not synced yet."},
    },
)
def indicator_series(
    session: SessionDep,
    country: CountryQuery,
    indicator: IndicatorQuery,
    start: PeriodQuery = None,
    end: PeriodQuery = None,
) -> IndicatorSeries:
    if get_country(country) is None:
        raise unsupported_country(country)
    ind = resolve_indicator(indicator)
    try:
        lo, hi = period_bound(start, end=False), period_bound(end, end=True)
    except ValueError as exc:  # e.g. 2026-13 or 2026-02-30 match the pattern but are not dates
        raise ApiError(422, "invalid_range", "`start`/`end` is not a valid period.") from exc
    if lo and hi and lo > hi:
        raise ApiError(422, "invalid_range", "`start` must not be after `end`.")

    data = load_indicator(session, country.upper(), ind)
    points = [
        (p, v)
        for p, v in data.points
        if (lo is None or period_start(p) >= lo) and (hi is None or period_start(p) <= hi)
    ]
    truncated = len(points) > MAX_POINTS
    points = points[-MAX_POINTS:]
    return IndicatorSeries(
        country=data.iso,
        indicator=indicator_definition(ind),
        unit=data.unit,
        transform=data.transform.description,
        scope_note=data.mapping.scope_note,
        note=data.mapping.note,
        points=[SeriesPoint(period=p, value=round(v, 6)) for p, v in points],
        truncated=truncated,
        provenance=provenance(session, data),
        quality=latest_checks(session, data.series_id),
    )
