"""ALFRED revisions: how US figures changed between their first release and today."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.schemas import ErrorResponse, Revisions
from macropulse_api.services.vintages import (
    VINTAGE_COUNTRY,
    VINTAGE_INDICATORS,
    VintagesUnavailableError,
    revisions,
)

router = APIRouter(prefix="/api/vintages", tags=["vintages"])

ERRORS = {
    422: {"model": ErrorResponse, "description": "Country or indicator without stored vintages."},
    503: {"model": ErrorResponse, "description": "Vintages not synced yet (needs FRED_API_KEY)."},
}


@router.get(
    "/revisions",
    response_model=Revisions,
    summary="First release versus current value per period (ALFRED vintages)",
    responses=ERRORS,  # type: ignore[arg-type]
)
def get_revisions(
    request: Request,
    session: SessionDep,
    country: Annotated[str, Query(pattern=r"^[A-Za-z]{2}$", description="ISO alpha-2 code.")],
    indicator: Annotated[str, Query(pattern=r"^[a-z0-9_]{1,40}$", description="Indicator id.")],
) -> Revisions:
    iso = country.upper()
    if iso != VINTAGE_COUNTRY:
        raise ApiError(
            422,
            "vintages_not_available",
            "Revision histories exist only for the United States (ALFRED). Eurostat and the ECB "
            "serve the latest revision only.",
            {"supported_countries": [VINTAGE_COUNTRY]},
        )
    if indicator not in VINTAGE_INDICATORS:
        raise ApiError(
            422,
            "unsupported_indicator",
            f"No revision history is stored for {indicator!r}.",
            {"supported": list(VINTAGE_INDICATORS)},
        )
    try:
        return Revisions(**revisions(session, iso, indicator))
    except VintagesUnavailableError:
        configured = request.app.state.settings.fred_api_key is not None
        raise ApiError(
            503,
            "vintages_not_synced",
            "No ALFRED vintages are stored yet. Run `uv run macropulse vintages-sync` on the server"
            + ("." if configured else " after setting FRED_API_KEY in the server environment."),
            {"fred_api_key_configured": configured},
        ) from None
