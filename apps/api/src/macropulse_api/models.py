"""ORM entities.

Phase 1 covers reference data and ingestion bookkeeping; observations arrive in Phase 3.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
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
