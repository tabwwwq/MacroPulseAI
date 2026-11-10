"""Crisis time machine: walk-forward replay of past as-of quarters and event tracking."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import CrisisPreset, ErrorResponse, Replay, ReplayEpisodes
from macropulse_api.services.replay import CRISES, episodes, replay
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
    "/episodes",
    response_model=ReplayEpisodes,
    summary="Realised technical recessions (warned / missed) and false alarms, out of sample",
    responses=ERRORS,  # type: ignore[arg-type]
)
def get_episodes(
    session: SessionDep, country: CountryQuery, horizon: HorizonQuery = 4
) -> ReplayEpisodes:
    return ReplayEpisodes(**episodes(session, _check(country, horizon), horizon))
