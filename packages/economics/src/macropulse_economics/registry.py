"""Static registry of supported geographies and official data sources.

This module holds *metadata only* (names, codes, documentation links, licence notes). It never holds
economic observations. A country's **target** support level states what the project aims to support;
its **current** support level is computed at runtime from the observations actually ingested, so the
UI can never advertise coverage that has not been retrieved and validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SupportLevel(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class PolicyRateScope(StrEnum):
    """Whether a country's policy rate is set nationally or shared across a currency union."""

    EURO_AREA_SHARED = "euro_area_shared"
    NATIONAL = "national"


@dataclass(frozen=True, slots=True)
class CountryDef:
    iso2: str
    iso3: str
    name: str
    region: str
    currency: str
    euro_area_member: bool
    policy_rate_scope: PolicyRateScope
    primary_gdp_source: str
    target_support: SupportLevel


@dataclass(frozen=True, slots=True)
class SourceDef:
    id: str
    name: str
    publisher: str
    base_url: str
    docs_url: str
    terms_url: str
    attribution: str
    requires_api_key: bool
    api_key_env: str | None = None


COUNTRIES: tuple[CountryDef, ...] = (
    CountryDef(
        iso2="BE",
        iso3="BEL",
        name="Belgium",
        region="Euro area",
        currency="EUR",
        euro_area_member=True,
        policy_rate_scope=PolicyRateScope.EURO_AREA_SHARED,
        primary_gdp_source="eurostat",
        target_support=SupportLevel.FULL,
    ),
    CountryDef(
        iso2="DE",
        iso3="DEU",
        name="Germany",
        region="Euro area",
        currency="EUR",
        euro_area_member=True,
        policy_rate_scope=PolicyRateScope.EURO_AREA_SHARED,
        primary_gdp_source="eurostat",
        target_support=SupportLevel.FULL,
    ),
    CountryDef(
        iso2="FR",
        iso3="FRA",
        name="France",
        region="Euro area",
        currency="EUR",
        euro_area_member=True,
        policy_rate_scope=PolicyRateScope.EURO_AREA_SHARED,
        primary_gdp_source="eurostat",
        target_support=SupportLevel.FULL,
    ),
    CountryDef(
        iso2="NL",
        iso3="NLD",
        name="Netherlands",
        region="Euro area",
        currency="EUR",
        euro_area_member=True,
        policy_rate_scope=PolicyRateScope.EURO_AREA_SHARED,
        primary_gdp_source="eurostat",
        target_support=SupportLevel.FULL,
    ),
    CountryDef(
        iso2="US",
        iso3="USA",
        name="United States",
        region="North America",
        currency="USD",
        euro_area_member=False,
        policy_rate_scope=PolicyRateScope.NATIONAL,
        primary_gdp_source="fred",
        target_support=SupportLevel.FULL,
    ),
)

SOURCES: tuple[SourceDef, ...] = (
    SourceDef(
        id="eurostat",
        name="Eurostat dissemination API",
        publisher="Eurostat (European Commission)",
        base_url="https://ec.europa.eu/eurostat/api/dissemination",
        docs_url="https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction",
        terms_url="https://ec.europa.eu/eurostat/about-us/policies/copyright",
        attribution="Source: Eurostat. Reuse authorised with acknowledgement of the source.",
        requires_api_key=False,
    ),
    SourceDef(
        id="ecb",
        name="ECB Data Portal API",
        publisher="European Central Bank",
        base_url="https://data-api.ecb.europa.eu/service",
        docs_url="https://data.ecb.europa.eu/help/api/overview",
        terms_url="https://www.ecb.europa.eu/services/disclaimer/html/index.en.html",
        attribution="Source: European Central Bank (ECB Data Portal).",
        requires_api_key=False,
    ),
    SourceDef(
        id="fred",
        name="FRED / ALFRED API",
        publisher="Federal Reserve Bank of St. Louis",
        base_url="https://api.stlouisfed.org/fred",
        docs_url="https://fred.stlouisfed.org/docs/api/fred/series_observations.html",
        terms_url="https://fred.stlouisfed.org/legal/",
        attribution=(
            "Source: FRED, Federal Reserve Bank of St. Louis. "
            "Series copyrights belong to their owners."
        ),
        requires_api_key=True,
        api_key_env="FRED_API_KEY",
    ),
    SourceDef(
        id="worldbank",
        name="World Bank Indicators API v2",
        publisher="The World Bank",
        base_url="https://api.worldbank.org/v2",
        docs_url="https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
        terms_url="https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets",
        attribution="Source: World Bank, World Development Indicators (CC BY 4.0).",
        requires_api_key=False,
    ),
    SourceDef(
        id="oecd",
        name="OECD Data Explorer (SDMX)",
        publisher="OECD",
        base_url="https://sdmx.oecd.org/public/rest",
        docs_url="https://data-explorer.oecd.org/",
        terms_url="https://www.oecd.org/en/about/terms-conditions.html",
        attribution="Source: OECD Data Explorer.",
        requires_api_key=False,
    ),
)

_COUNTRY_INDEX = {c.iso2: c for c in COUNTRIES}


def get_country(iso2: str) -> CountryDef | None:
    """Return the registry entry for an ISO 3166-1 alpha-2 code (case-insensitive), if supported."""
    return _COUNTRY_INDEX.get(iso2.upper())
