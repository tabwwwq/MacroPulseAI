"""Indicator forecasts with rolling-origin backtests and empirical intervals."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from macropulse_api.deps import SessionDep
from macropulse_api.ratelimit import compute_limit
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import ErrorResponse, ForecastResponse
from macropulse_api.services.forecasts import forecast
from macropulse_economics import get_country

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.get(
    "",
    response_model=ForecastResponse,
    summary="Forecast of real GDP growth, inflation or unemployment with backtest diagnostics",
    responses={
        404: {"model": ErrorResponse, "description": "Not enough published history."},
        422: {"model": ErrorResponse, "description": "Unsupported country, metric or horizon."},
        429: {"model": ErrorResponse, "description": "Too many compute requests."},
        503: {"model": ErrorResponse, "description": "Series not synced."},
    },
    dependencies=[Depends(compute_limit)],
)
def get_forecast(
    session: SessionDep,
    country: Annotated[str, Query(pattern=r"^[A-Za-z]{2}$")],
    metric: Annotated[str, Query(pattern=r"^[a-z0-9_]{2,40}$")],
    horizon: Annotated[int, Query(description="Quarters ahead: 1, 2, 4 or 8.")] = 4,
    as_of: Annotated[str | None, Query(pattern=r"^\d{4}-Q[1-4]$")] = None,
) -> ForecastResponse:
    if get_country(country) is None:
        raise unsupported_country(country)
    return ForecastResponse(**forecast(session, country.upper(), metric, horizon, as_of))
