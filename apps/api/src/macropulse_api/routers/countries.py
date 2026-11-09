"""Supported geographies and their *current* (data-derived) support level."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Path as PathParam
from sqlalchemy import select

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.models import Country as CountryRow
from macropulse_api.schemas import Country, CountryList, ErrorResponse
from macropulse_api.services.coverage import country_support
from macropulse_economics import COUNTRIES, PolicyRateScope, get_country

router = APIRouter(prefix="/api/countries", tags=["countries"])

Iso2 = Annotated[
    str,
    PathParam(
        pattern=r"^[A-Za-z]{2}$",
        description="ISO 3166-1 alpha-2 code (case-insensitive).",
        examples=["DE"],
    ),
]
_ORDER = {c.iso2: i for i, c in enumerate(COUNTRIES)}


def _to_schema(row: CountryRow) -> Country:
    return Country(
        iso2=row.iso2,
        iso3=row.iso3,
        name=row.name,
        region=row.region,
        currency=row.currency,
        euro_area_member=row.euro_area_member,
        policy_rate_scope=PolicyRateScope(row.policy_rate_scope),
        primary_gdp_source=row.primary_gdp_source,
        support=country_support(row),
    )


def unsupported_country(iso2: str) -> ApiError:
    return ApiError(
        status_code=422,
        code="unsupported_country",
        message=f"Country '{iso2.upper()}' is not supported.",
        details={"supported": [c.iso2 for c in COUNTRIES]},
    )


@router.get("", response_model=CountryList, summary="List supported countries")
def list_countries(session: SessionDep) -> CountryList:
    rows = session.scalars(select(CountryRow)).all()
    items = [_to_schema(r) for r in sorted(rows, key=lambda r: _ORDER.get(r.iso2, 99))]
    return CountryList(items=items, count=len(items))


@router.get(
    "/{iso2}",
    response_model=Country,
    summary="Get one country",
    responses={422: {"model": ErrorResponse, "description": "Malformed or unsupported code."}},
)
def get_one(iso2: Iso2, session: SessionDep) -> Country:
    if get_country(iso2) is None:
        raise unsupported_country(iso2)
    row = session.get(CountryRow, iso2.upper())
    if row is None:  # registry not synced into this database yet
        raise ApiError(
            status_code=503,
            code="registry_not_synced",
            message="Country registry is not loaded. Run `uv run macropulse db upgrade`.",
        )
    return _to_schema(row)
