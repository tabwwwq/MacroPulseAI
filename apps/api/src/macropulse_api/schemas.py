"""Public API contract (Pydantic v2). The frontend's TypeScript types are generated from these."""

from __future__ import annotations

from datetime import date, datetime
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


# ------------------------------------------------------------------ indicator series


class SeriesPoint(BaseModel):
    period: str
    value: float


class SeriesProvenance(BaseModel):
    source_id: str
    source_name: str
    docs_url: str | None
    dataset: str
    series_key: str
    series_id: str
    native_unit: str
    adjustment: str | None
    request_url: str = Field(description="Exact request used for the latest successful fetch.")
    retrieved_at: datetime | None = Field(description="Last successful fetch (data freshness).")
    source_updated_at: str | None = Field(
        description="Dataset update stamp reported by the source."
    )
    native_observations: int


QualityStatus = Literal["pass", "warn", "fail"]


class QualityCheckResult(BaseModel):
    rule: str
    status: QualityStatus
    detail: str


class IndicatorSeries(BaseModel):
    country: str
    indicator: IndicatorDefinition
    unit: str
    transform: str = Field(description="How the shown values are derived from the native series.")
    scope_note: str
    note: str
    points: list[SeriesPoint]
    truncated: bool = Field(description="True when only the most recent points were returned.")
    provenance: SeriesProvenance
    quality: list[QualityCheckResult] = Field(
        description="Checks from the latest ingestion run that attempted this series."
    )


# ------------------------------------------------------------------ country summary (KPIs)

KpiStatus = Literal["ok", "no_data", "unavailable"]


class KpiValue(BaseModel):
    indicator: IndicatorDefinition
    status: KpiStatus = Field(
        description="`ok`: a stored value exists; `no_data`: mapped but nothing stored for the "
        "cut-off; `unavailable`: not published, not mapped or no connector."
    )
    reason: str | None = Field(description="Why there is no value (when status is not `ok`).")
    value: float | None
    period: str | None = Field(description="Reference period of `value`.")
    previous_value: float | None
    previous_period: str | None
    change: float | None = Field(
        description="`value - previous_value` in the unit of `unit` (percentage points for rates)."
    )
    unit: str
    transform: str | None = Field(description="How `value` is derived from the native series.")
    scope_note: str
    source_flag: str | None = Field(
        description="Source status flag on the observation, e.g. p = provisional, e = estimated."
    )
    days_since_period_end: int | None = Field(description="Age at the cut-off date.")
    stale: bool = Field(description="Older than the release-cycle limit for its frequency.")
    provenance: SeriesProvenance | None


class CountrySummary(BaseModel):
    country: str
    as_of: str | None = Field(description="Requested as-of quarter; `null` means latest.")
    cutoff: date = Field(description="Only reference periods ending on or before this date.")
    data_basis: str = Field(description="What the values are (and are not): revisions, vintages.")
    freshness: datetime | None = Field(description="Most recent successful fetch behind the KPIs.")
    kpis: list[KpiValue]
    generated_at: datetime


# ------------------------------------------------------------------ data quality / lineage

SeriesHealth = Literal["not_synced", "pass", "warn", "fail"]


class StoredSeries(BaseModel):
    series_id: str
    source_id: str
    source_name: str
    dataset: str
    series_key: str
    geo: str
    frequency: str
    unit: str
    adjustment: str | None
    indicators: list[str] = Field(description="Indicators derived from this native series.")
    countries: list[str] = Field(description="Countries served (the ECB rate serves several).")
    mapping_status: MappingStatusValue
    observations: int
    first_period: str | None
    last_period: str | None
    retrieved_at: datetime | None = Field(description="Last successful fetch.")
    source_updated_at: str | None
    request_url: str | None
    last_checked_run_id: int | None
    health: SeriesHealth = Field(description="Worst result of the latest checks.")
    quality: list[QualityCheckResult]
    export_path: str = Field(description="API path of the raw-observation CSV.")


class DataQualityReport(BaseModel):
    country: str | None
    items: list[StoredSeries]
    counts: dict[str, int] = Field(description="Number of series per health status.")
    generated_at: datetime


# ------------------------------------------------------------------ models (Phase 5)


class MetricValue(BaseModel):
    split: str = Field(description="development (2000-2014) or heldout (2015 onwards).")
    segment: str = Field(description="`all` or an ISO2 country.")
    metric: str
    value: float | None = Field(description="NULL when undefined for this split; see `note`.")
    n: int
    events: int
    note: str | None = None
    detail: Any | None = Field(default=None, description="Calibration bins or confusion counts.")


class ModelSummary(BaseModel):
    id: str
    run_id: str
    horizon: int
    model_key: str
    name: str
    role: str = Field(description="baseline or candidate")
    status: str = Field(description="evaluated or unavailable")
    selected: bool = Field(description="Published model of its run and horizon.")
    unavailable_reason: str | None
    created_at: datetime
    target_version: str
    feature_set_version: str
    training_rows: int | None
    training_events: int | None
    training_last_as_of: str | None
    data_snapshot: str
    code_revision: str | None
    artifact_available: bool
    headline: dict[str, dict[str, float | None]] = Field(
        description="Per split: brier, brier_skill, log_loss, roc_auc, pr_auc (None = undefined)."
    )
    selection_note: str | None
    heldout_check: dict[str, Any] | None


class ModelList(BaseModel):
    run_id: str | None
    items: list[ModelSummary]
    note: str


class ModelDetail(ModelSummary):
    feature_names: list[str]
    params: dict[str, Any]
    evaluation: dict[str, Any]
    label_cutoff: dict[str, Any]
    seed: int
    command: str
    library_versions: dict[str, Any]
    coefficients: dict[str, Any] | None
    calibrated_folds: int | None
    metrics: list[MetricValue]


# ------------------------------------------------------------------ recession estimates (Phase 6)


class RiskBand(BaseModel):
    upper: float = Field(description="Probabilities below this value fall in the band.")
    name: str


class EstimateModel(BaseModel):
    id: str
    name: str
    key: str
    run_id: str
    trained_at: datetime | None
    training_rows: int | None
    training_events: int | None
    training_last_as_of: str | None = Field(
        description="Latest as-of quarter whose label was used."
    )
    gdp_observed_to: str | None
    target_version: str
    feature_set_version: str
    code_revision: str | None


class Contribution(BaseModel):
    feature: str
    label: str
    value: float
    period: str | None = Field(description="Reference period of the input value.")
    contribution: float
    standardised_value: float | None = None
    training_mean: float | None
    outside_training_range: bool
    unusual: bool = Field(description="Outside the 5th to 95th percentile of the training sample.")


class EstimateExplanation(BaseModel):
    method: str
    unit: str = Field(description="log-odds (additive) or probability (local sensitivity)")
    intercept: float | None
    note: str
    items: list[Contribution]


class EstimateOutcome(BaseModel):
    status: str = Field(description="observed, censored (future not yet known) or missing")
    label: int | None
    window: list[str]


class RecessionEstimate(BaseModel):
    country: str
    horizon: int
    as_of: str
    requested_as_of: str | None
    cutoff: date
    probability: float
    band: str
    bands: list[RiskBand]
    base_rate: float | None = Field(description="Event rate in the model's training sample.")
    model: EstimateModel
    prediction_timestamp: datetime
    data_freshness: datetime | None = Field(description="Latest fetch of the inputs used.")
    inputs_stale: list[str]
    explanation: EstimateExplanation
    track_record: dict[str, Any] = Field(description="Development and held-out Brier/skill/AUC.")
    selection_note: str | None
    in_sample: bool = Field(
        description="True when this as-of quarter's outcome was in the training data: a fit, not a "
        "forecast. Use the walk-forward probability for an honest historical estimate."
    )
    outcome: EstimateOutcome
    walk_forward_probability: float | None
    walk_forward_split: str | None
    stored_estimate: float | None = Field(
        description="Probability stored at training time for this as-of (round-trip check)."
    )
    event_definition: str
    limitations: list[str]


class HistoryPoint(BaseModel):
    as_of: str
    probability: float
    label: int | None
    split: str
    fold_year: int | None


class RecessionSpan(BaseModel):
    start: str
    end: str


class RecessionHistory(BaseModel):
    country: str
    horizon: int
    model_id: str
    model_name: str
    points: list[HistoryPoint]
    baseline: list[HistoryPoint] = Field(description="Prevalence baseline, same folds.")
    recessions: list[RecessionSpan] = Field(description="Technical recessions in stored GDP.")
    note: str


class CurvePoint(BaseModel):
    x: float
    y: float


class SplitCurves(BaseModel):
    split: str
    n: int
    events: int
    roc: list[CurvePoint] | None = Field(description="False-positive rate (x) vs recall (y).")
    pr: list[CurvePoint] | None = Field(description="Recall (x) vs precision (y).")
    note: str | None


class ModelCurves(BaseModel):
    model_id: str
    splits: list[SplitCurves]
