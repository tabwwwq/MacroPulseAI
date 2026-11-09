"""`GET /api/countries/{iso2}/summary`: headline KPIs with their latest stored value, the change
since the previous period, staleness and full provenance — or an explicit reason for no value."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Query

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.routers.countries import Iso2, unsupported_country
from macropulse_api.schemas import CountrySummary, ErrorResponse, KpiValue
from macropulse_api.services.series_data import (
    indicator_definition,
    load_indicator,
    provenance,
)
from macropulse_economics import get_country
from macropulse_economics.indicators import INDICATORS, IndicatorDef
from macropulse_economics.periods import days_since_end, period_end
from macropulse_economics.quality import MAX_AGE_DAYS

router = APIRouter(prefix="/api/countries", tags=["countries"])

AsOfQuery = Annotated[
    str | None,
    Query(
        pattern=r"^\d{4}-Q[1-4]$",
        description="Information cut-off quarter (YYYY-Qn). Omit for the latest stored data.",
    ),
]

LATEST_BASIS = (
    "Latest stored revision of each official series (last successful sync). Values are revised "
    "data, not the figures first published."
)


def _as_of_basis(cutoff: date) -> str:
    return (
        f"Latest revised values for reference periods that ended on or before {cutoff}. "
        "Publication lags are not applied and no historical vintages are used, so some of these "
        "values were not yet published, or have since been revised, relative to that date."
    )


def cutoff_for(as_of: str | None, today: date) -> date:
    if as_of is None:
        return today
    end = period_end(as_of)
    if date(int(as_of[:4]), (int(as_of[-1]) - 1) * 3 + 1, 1) > today:
        raise ApiError(422, "invalid_as_of", f"As-of quarter {as_of} is in the future.")
    return min(end, today)


def kpi_value(session: SessionDep, iso: str, ind: IndicatorDef, cutoff: date) -> KpiValue:
    empty = {
        "indicator": indicator_definition(ind),
        "value": None,
        "period": None,
        "previous_value": None,
        "previous_period": None,
        "change": None,
        "unit": ind.unit,
        "transform": None,
        "scope_note": "",
        "source_flag": None,
        "days_since_period_end": None,
        "stale": False,
        "provenance": None,
    }
    try:
        data = load_indicator(session, iso, ind)
    except ApiError as exc:
        status = "no_data" if exc.status_code == 503 else "unavailable"
        return KpiValue(status=status, reason=exc.message, **empty)

    eligible = [(p, v) for p, v in data.points if period_end(p) <= cutoff]
    base = {
        **empty,
        "transform": data.transform.description,
        "scope_note": data.mapping.scope_note,
        "provenance": provenance(session, data),
    }
    if not eligible:
        return KpiValue(
            status="no_data",
            reason=f"No stored observation for a period ending on or before {cutoff}.",
            **base,
        )
    period, value = eligible[-1]
    prev = eligible[-2] if len(eligible) > 1 else None
    flags = {r.period: r.obs_status for r in data.rows}
    age = days_since_end(period, cutoff)
    limit = MAX_AGE_DAYS.get(data.mapping.native_frequency.value)
    return KpiValue(
        **{
            **base,
            "status": "ok",
            "reason": None,
            "value": round(value, 6),
            "period": period,
            "previous_value": round(prev[1], 6) if prev else None,
            "previous_period": prev[0] if prev else None,
            "change": round(value - prev[1], 6) if prev else None,
            "source_flag": flags.get(period),
            "days_since_period_end": age,
            "stale": limit is not None and age > limit,
        }
    )


@router.get(
    "/{iso2}/summary",
    response_model=CountrySummary,
    summary="Headline KPIs with latest stored values and provenance",
    responses={422: {"model": ErrorResponse, "description": "Unsupported country or as-of."}},
)
def country_summary(session: SessionDep, iso2: Iso2, as_of: AsOfQuery = None) -> CountrySummary:
    if get_country(iso2) is None:
        raise unsupported_country(iso2)
    iso = iso2.upper()
    now = datetime.now(UTC)
    cutoff = cutoff_for(as_of, now.date())
    kpis = [kpi_value(session, iso, ind, cutoff) for ind in INDICATORS if ind.kpi]
    fetched = [
        k.provenance.retrieved_at for k in kpis if k.provenance and k.provenance.retrieved_at
    ]
    return CountrySummary(
        country=iso,
        as_of=as_of,
        cutoff=cutoff,
        data_basis=LATEST_BASIS if as_of is None else _as_of_basis(cutoff),
        freshness=max(fetched) if fetched else None,
        kpis=kpis,
        generated_at=now,
    )
