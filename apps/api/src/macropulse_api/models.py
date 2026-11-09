"""ORM entities.

Phase 1 covers reference data and ingestion bookkeeping; observations arrive in Phase 3.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
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
