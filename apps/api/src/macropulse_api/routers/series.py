"""`GET /api/indicators`: stored official series for one country and indicator, with derivation,
provenance and the quality checks of the latest ingestion run."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated, cast

from fastapi import APIRouter, Query
from sqlalchemy import select

from macropulse_api.db import as_utc
from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.models import DataSource, Observation, QualityCheck
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import (
    ErrorResponse,
    IndicatorDefinition,
    IndicatorSeries,
    QualityCheckResult,
    QualityStatus,
    SeriesPoint,
    SeriesProvenance,
)
from macropulse_api.services.coverage import SYNC_HINT
from macropulse_economics import get_country
from macropulse_economics.connectors import CONNECTORS
from macropulse_economics.indicators import INDICATORS, get_indicator, mappings_for
from macropulse_economics.periods import period_start, shift
from macropulse_economics.series import SYNCABLE, series_id_for
from macropulse_economics.transforms import apply as apply_transform
from macropulse_economics.transforms import transform_for

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
    iso = country.upper()
    ind = get_indicator(indicator)
    if ind is None:
        raise ApiError(
            422,
            "unsupported_indicator",
            f"Indicator '{indicator}' is not supported.",
            {"supported": [i.id for i in INDICATORS]},
        )
    try:
        lo, hi = period_bound(start, end=False), period_bound(end, end=True)
    except ValueError as exc:  # e.g. 2026-13 or 2026-02-30 match the pattern but are not dates
        raise ApiError(422, "invalid_range", "`start`/`end` is not a valid period.") from exc
    if lo and hi and lo > hi:
        raise ApiError(422, "invalid_range", "`start` must not be after `end`.")

    m = mappings_for(iso).get(ind.id)
    if m is None or m.status not in SYNCABLE:
        reason = (m.note if m else "") or "No official source is mapped for this country."
        raise ApiError(404, "indicator_unavailable", reason)
    if m.source_id not in CONNECTORS:
        raise ApiError(404, "indicator_unavailable", f"No {m.source_id} connector yet.")

    sid = series_id_for(m)
    rows = session.scalars(
        select(Observation).where(Observation.series_id == sid).order_by(Observation.period_start)
    ).all()
    if not rows:
        raise ApiError(503, "data_not_synced", f"No observations stored for {sid}. {SYNC_HINT}")

    transform = transform_for(ind.id, m.source_id)
    derived = apply_transform(transform, [(r.period, r.value) for r in rows])
    points = [
        (p, v)
        for p, v in derived
        if (lo is None or period_start(p) >= lo) and (hi is None or period_start(p) <= hi)
    ]
    truncated = len(points) > MAX_POINTS
    points = points[-MAX_POINTS:]

    latest = max(rows, key=lambda r: r.retrieved_at)
    last_run = max(r.ingestion_run_id for r in rows)
    checks = session.scalars(
        select(QualityCheck)
        .where(QualityCheck.series_id == sid, QualityCheck.ingestion_run_id == last_run)
        .order_by(QualityCheck.id)
    ).all()
    source = session.get(DataSource, m.source_id)
    return IndicatorSeries(
        country=iso,
        indicator=IndicatorDefinition(
            id=ind.id,
            name=ind.name,
            category=ind.category.value,
            unit=ind.unit,
            frequency=ind.frequency.value,
            description=ind.description,
            kpi=ind.kpi,
        ),
        unit=ind.unit if transform.kind == "growth" else latest.unit,
        transform=transform.description,
        scope_note=m.scope_note,
        note=m.note,
        points=[SeriesPoint(period=p, value=round(v, 6)) for p, v in points],
        truncated=truncated,
        provenance=SeriesProvenance(
            source_id=m.source_id,
            source_name=source.name if source else m.source_id,
            docs_url=source.docs_url if source else None,
            dataset=m.dataset,
            series_key=m.series_key,
            series_id=sid,
            native_unit=latest.unit,
            adjustment=latest.adjustment,
            request_url=latest.source_url,
            retrieved_at=as_utc(latest.retrieved_at),
            source_updated_at=latest.source_updated_at,
            native_observations=len(rows),
        ),
        quality=[
            QualityCheckResult(rule=c.rule, status=cast(QualityStatus, c.status), detail=c.detail)
            for c in checks
        ],
    )
