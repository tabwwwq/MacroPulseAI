"""Crisis time machine: walk-forward replay of past as-of quarters and event tracking."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.ratelimit import compute_limit
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import (
    CrisisPreset,
    ErrorResponse,
    Replay,
    ReplayEpisodes,
    VintageReplay,
)
from macropulse_api.services.replay import CRISES, episodes, replay
from macropulse_api.services.vintage_replay import vintage_replay
from macropulse_api.services.vintages import VINTAGE_COUNTRY
from macropulse_economics import get_country

router = APIRouter(prefix="/api/history", tags=["history"])

CountryQuery = Annotated[str, Query(pattern=r"^[A-Za-z]{2}$", description="ISO alpha-2 code.")]
HorizonQuery = Annotated[int, Query(description="Quarters ahead: 2 or 4.")]
ERRORS = {
    404: {"model": ErrorResponse, "description": "No out-of-sample estimate for this quarter."},
    422: {"model": ErrorResponse, "description": "Unsupported country, horizon or as-of."},
    503: {"model": ErrorResponse, "description": "No trained model / synced data."},
}


def _check(country: str, horizon: int) -> str:
    if get_country(country) is None:
        raise unsupported_country(country)
    if horizon not in (2, 4):
        raise ApiError(
            422, "unsupported_horizon", "Horizon must be 2 or 4 quarters.", {"supported": [2, 4]}
        )
    return country.upper()


@router.get("/presets", response_model=list[CrisisPreset], summary="Suggested crisis dates")
def presets() -> list[CrisisPreset]:
    return [CrisisPreset(as_of=q, label=label) for q, label in CRISES]


@router.get(
    "/replay",
    response_model=Replay,
    summary="What the walk-forward model said at a past as-of quarter, and what followed",
    responses=ERRORS,  # type: ignore[arg-type]
)
def get_replay(
    request: Request,
    session: SessionDep,
    country: CountryQuery,
    as_of: Annotated[str, Query(pattern=r"^\d{4}-Q[1-4]$", description="Replay quarter.")],
    horizon: HorizonQuery = 4,
) -> Replay:
    iso = _check(country, horizon)
    configured = request.app.state.settings.fred_api_key is not None
    return Replay(**replay(session, iso, horizon, as_of, fred_key_configured=configured))


@router.get(
    "/vintage-replay",
    response_model=VintageReplay,
    summary="US only: the same walk-forward fold model scored on the figures as first published",
    responses={
        **ERRORS,  # type: ignore[dict-item]
        429: {"model": ErrorResponse, "description": "Too many compute requests."},
    },
    dependencies=[Depends(compute_limit)],
)
def get_vintage_replay(
    session: SessionDep,
    country: CountryQuery,
    as_of: Annotated[str, Query(pattern=r"^\d{4}-Q[1-4]$", description="Replay quarter.")],
    horizon: HorizonQuery = 4,
) -> VintageReplay:
    iso = _check(country, horizon)
    if iso != VINTAGE_COUNTRY:
        raise ApiError(
            422,
            "vintages_not_available",
            "Figures as first published are stored only for the United States (ALFRED). Eurostat "
            "and the ECB serve the latest revision only.",
            {"supported_countries": [VINTAGE_COUNTRY]},
        )
    return VintageReplay(**vintage_replay(session, horizon, as_of))


@router.get(
    "/episodes",
    response_model=ReplayEpisodes,
    summary="Realised technical recessions (warned / missed) and false alarms, out of sample",
    responses=ERRORS,  # type: ignore[arg-type]
)
def get_episodes(
    session: SessionDep, country: CountryQuery, horizon: HorizonQuery = 4
) -> ReplayEpisodes:
    return ReplayEpisodes(**episodes(session, _check(country, horizon), horizon))
