"""Scenario lab: bounded, exploratory sensitivity of the published recession model."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.ratelimit import compute_limit
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import (
    ErrorResponse,
    ScenarioRequest,
    ScenarioResult,
    ScenarioSpec,
    ShockSpec,
)
from macropulse_api.services.scenarios import DISCLAIMER, SHOCKS, evaluate
from macropulse_economics import get_country

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("/spec", response_model=ScenarioSpec, summary="Available shocks, bounds and mapping")
def scenario_spec() -> ScenarioSpec:
    return ScenarioSpec(
        shocks=[
            ShockSpec(
                key=s.key,
                label=s.label,
                unit=s.unit,
                minimum=s.minimum,
                maximum=s.maximum,
                step=s.step,
                effect=s.effect,
            )
            for s in SHOCKS
        ],
        disclaimer=DISCLAIMER,
    )


@router.post(
    "/evaluate",
    response_model=ScenarioResult,
    summary="Baseline vs shocked recession probability (sensitivity, not causal simulation)",
    responses={
        404: {"model": ErrorResponse, "description": "Inputs not available for the as-of."},
        422: {"model": ErrorResponse, "description": "Invalid country, horizon or shock."},
        429: {"model": ErrorResponse, "description": "Too many compute requests."},
        503: {"model": ErrorResponse, "description": "No trained model / artifact."},
    },
    dependencies=[Depends(compute_limit)],
)
def evaluate_scenario(
    request: Request, session: SessionDep, body: ScenarioRequest
) -> ScenarioResult:
    if get_country(body.country) is None:
        raise unsupported_country(body.country)
    if body.horizon not in (2, 4):
        raise ApiError(
            422, "unsupported_horizon", "Horizon must be 2 or 4 quarters.", {"supported": [2, 4]}
        )
    result = evaluate(
        session,
        body.country.upper(),
        body.horizon,
        body.as_of,
        body.shocks.model_dump(),
        models_dir=request.app.state.settings.models_dir,
    )
    return ScenarioResult(**result)
