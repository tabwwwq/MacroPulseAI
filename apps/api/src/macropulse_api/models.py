"""ORM entities.

Reference data, ingestion bookkeeping and observations (Phases 1 to 3); model versions, metrics
and predictions (Phase 5).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from macropulse_api.db import Base, utcnow


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Country(TimestampMixin, Base):
    __tablename__ = "countries"

    iso2: Mapped[str] = mapped_column(String(2), primary_key=True)
    iso3: Mapped[str] = mapped_column(String(3), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(3))
    euro_area_member: Mapped[bool] = mapped_column(Boolean)
    policy_rate_scope: Mapped[str] = mapped_column(String(32))
    primary_gdp_source: Mapped[str] = mapped_column(String(32))
    target_support: Mapped[str] = mapped_column(String(16))


class DataSource(TimestampMixin, Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    publisher: Mapped[str] = mapped_column(String(120))
    base_url: Mapped[str] = mapped_column(String(300))
    docs_url: Mapped[str] = mapped_column(String(300))
    terms_url: Mapped[str] = mapped_column(String(300))
    attribution: Mapped[str] = mapped_column(Text)
    requires_api_key: Mapped[bool] = mapped_column(Boolean)
    api_key_env: Mapped[str | None] = mapped_column(String(64), nullable=True)


class IngestionRun(Base):
    """One attempt to sync a source. Source health/freshness is derived from these rows only."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # running | succeeded | partial | failed
    status: Mapped[str] = mapped_column(String(16))
    rows_upserted: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # live = fetched from the source now; snapshot = imported from a captured snapshot (demo)
    mode: Mapped[str] = mapped_column(String(16), default="live", server_default="live")
    # for snapshots: when the snapshot's data was originally retrieved from the sources
    snapshot_taken_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Observation(Base):
    """One official value of one native source series at one period (latest revision).

    `series_id` = "<source>:<dataset>:<series key>:<geo>" identifies the native series exactly as
    fetched; derived indicators (q/q growth, y/y rates) are computed from these rows, never stored
    in their place. Missing official values are simply absent — never filled.
    """

    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint("series_id", "period", name="uq_observations_series_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(200), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id", ondelete="CASCADE"))
    geo: Mapped[str] = mapped_column(String(8), index=True)
    dataset: Mapped[str] = mapped_column(String(64))
    series_key: Mapped[str] = mapped_column(String(200))
    period: Mapped[str] = mapped_column(String(10))  # "2026-Q3", "2026-10" or "2026-09-16"
    period_start: Mapped[date] = mapped_column(Date)
    frequency: Mapped[str] = mapped_column(String(10))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(64))
    adjustment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    obs_status: Mapped[str | None] = mapped_column(String(16), nullable=True)  # e.g. p, e, b
    source_url: Mapped[str] = mapped_column(Text)
    source_updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True
    )


class QualityCheck(Base):
    """Result of one data-quality rule for one series in one ingestion run."""

    __tablename__ = "quality_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[int] = mapped_column(
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True
    )
    series_id: Mapped[str] = mapped_column(String(200), index=True)
    rule: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(8))  # pass | warn | fail
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelVersion(Base):
    """One evaluated model (or a model that could not run) from one training run and horizon.

    Everything needed to reproduce it is recorded: target/feature versions, protocol, data snapshot
    hash, seed, command, code revision and library versions. Only the selected model of a run has a
    saved artifact.
    """

    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(40), index=True)
    horizon: Mapped[int] = mapped_column(Integer)
    model_key: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(16))  # baseline | candidate
    status: Mapped[str] = mapped_column(String(16))  # evaluated | unavailable
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    unavailable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    target_version: Mapped[str] = mapped_column(String(40))
    feature_set_version: Mapped[str] = mapped_column(String(40))
    feature_names: Mapped[list[str]] = mapped_column(JSON)
    params: Mapped[dict[str, Any]] = mapped_column(JSON)
    evaluation: Mapped[dict[str, Any]] = mapped_column(JSON)
    training_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_events: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_last_as_of: Mapped[str | None] = mapped_column(String(8), nullable=True)
    label_cutoff: Mapped[dict[str, Any]] = mapped_column(JSON)
    data_snapshot: Mapped[str] = mapped_column(String(80))
    data_retrieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    seed: Mapped[int] = mapped_column(Integer)
    command: Mapped[str] = mapped_column(Text)
    code_revision: Mapped[str | None] = mapped_column(String(60), nullable=True)
    library_versions: Mapped[dict[str, Any]] = mapped_column(JSON)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    coefficients: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    calibrated_folds: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ModelMetric(Base):
    """A measured metric for one model version, split and segment (`all` or an ISO2 country).
    `value` is NULL when the metric is undefined; `note` says why."""

    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[str] = mapped_column(
        ForeignKey("model_versions.id", ondelete="CASCADE"), index=True
    )
    split: Mapped[str] = mapped_column(String(20))  # development | heldout
    segment: Mapped[str] = mapped_column(String(8))
    metric: Mapped[str] = mapped_column(String(30))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    n: Mapped[int] = mapped_column(Integer)
    events: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[Any | None] = mapped_column(JSON, nullable=True)


class ModelPrediction(Base):
    """Out-of-sample walk-forward predictions (with the realised label when observed) and the
    selected model's current estimate per country (`split = live`)."""

    __tablename__ = "model_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[str] = mapped_column(
        ForeignKey("model_versions.id", ondelete="CASCADE"), index=True
    )
    country: Mapped[str] = mapped_column(String(2), index=True)
    as_of: Mapped[str] = mapped_column(String(8))
    horizon: Mapped[int] = mapped_column(Integer)
    probability: Mapped[float] = mapped_column(Float)
    label: Mapped[int | None] = mapped_column(Integer, nullable=True)
    split: Mapped[str] = mapped_column(String(12))  # development | heldout | unlabelled | live
    fold_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
