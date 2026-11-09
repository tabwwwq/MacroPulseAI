"""Public API contract (Pydantic v2). The frontend's TypeScript types are generated from these."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from macropulse_economics import PolicyRateScope, SupportLevel

# ------------------------------------------------------------------ errors


class ErrorBody(BaseModel):
    code: str = Field(description="Stable machine-readable error code, e.g. `unsupported_country`.")
    message: str = Field(description="Human-readable, safe-to-display explanation.")
    details: dict[str, Any] | None = None
    request_id: str | None = Field(default=None, description="Echo of the X-Request-ID header.")


class ErrorResponse(BaseModel):
    error: ErrorBody


# ------------------------------------------------------------------ health


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str
    time_utc: datetime


class ReadinessCheck(BaseModel):
    name: str
    ok: bool
    detail: str


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: list[ReadinessCheck]


# ------------------------------------------------------------------ countries


class CountrySupport(BaseModel):
    level: SupportLevel = Field(description="Current level, computed from ingested observations.")
    target: SupportLevel = Field(description="Level the project aims to support for this country.")
    reason: str


class Country(BaseModel):
    iso2: str
    iso3: str
    name: str
    region: str
    currency: str
    euro_area_member: bool
    policy_rate_scope: PolicyRateScope = Field(
        description="`euro_area_shared`: the ECB rate applies to all euro area members; "
        "it is not a national central-bank rate."
    )
    primary_gdp_source: str
    support: CountrySupport


class CountryList(BaseModel):
    items: list[Country]
    count: int


# ------------------------------------------------------------------ sources

SourceSyncStatus = Literal["never_synced", "running", "ok", "degraded", "failed"]


class SourceStatus(BaseModel):
    id: str
    name: str
    publisher: str
    docs_url: str
    terms_url: str
    attribution: str
    requires_api_key: bool
    api_key_configured: bool | None = Field(
        description="Whether the server has the key configured (the key itself is never exposed). "
        "`null` when the source needs no key."
    )
    status: SourceSyncStatus
    last_attempt_at: datetime | None = Field(description="Start of the most recent sync attempt.")
    last_success_at: datetime | None = Field(
        description="Data freshness = finish time of the last successful fetch. This is not the "
        "observation reference period and not the source's publication date."
    )
    last_rows_upserted: int | None
    last_error: str | None


class SourceStatusList(BaseModel):
    items: list[SourceStatus]
    generated_at: datetime


# ------------------------------------------------------------------ indicator catalog

IndicatorCategory = Literal[
    "growth", "prices", "labor", "monetary", "fiscal", "leading", "reference"
]
IndicatorFrequency = Literal["monthly", "quarterly", "annual", "event", "daily"]
MappingStatusValue = Literal["verified", "partial", "stale", "not_published", "unmapped"]


class IndicatorDefinition(BaseModel):
    id: str
    name: str
    category: IndicatorCategory
    unit: str
    frequency: IndicatorFrequency
    description: str
    kpi: bool = Field(description="Shown as a headline KPI tile.")


class SourceMappingInfo(BaseModel):
    status: MappingStatusValue = Field(
        description="What the live feasibility probe observed for this country/indicator: "
        "`verified` series returned, `partial` values without full metadata, `stale` series out "
        "of date, `not_published` by the source for this geography, `unmapped` not mapped yet."
    )
    source_id: str | None
    source_name: str | None
    docs_url: str | None
    dataset: str | None
    series_key: str | None
    native_frequency: IndicatorFrequency | None
    adjustment: str | None
    probe_last_period: str | None = Field(
        description="Latest period seen by the probe — metadata, not an ingested observation."
    )
    probe_date: str | None
    note: str
    scope_note: str


class IngestionState(BaseModel):
    observations: int = Field(description="Observations stored for this country/indicator.")
    latest_period: str | None
    source_last_success_at: datetime | None = Field(
        description="Last successful fetch of the mapped source (data freshness)."
    )


class CatalogEntry(BaseModel):
    indicator: IndicatorDefinition
    mapping: SourceMappingInfo
    ingestion: IngestionState


class CountryCatalog(BaseModel):
    country: str
    items: list[CatalogEntry]


class IndicatorCatalog(BaseModel):
    probe_date: str
    countries: list[CountryCatalog]
