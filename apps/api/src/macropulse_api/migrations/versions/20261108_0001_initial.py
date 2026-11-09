"""Initial schema: countries, data_sources, ingestion_runs.

Revision ID: 0001
Revises:
Create Date: 2026-11-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("iso2", sa.String(2), nullable=False),
        sa.Column("iso3", sa.String(3), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("euro_area_member", sa.Boolean(), nullable=False),
        sa.Column("policy_rate_scope", sa.String(32), nullable=False),
        sa.Column("primary_gdp_source", sa.String(32), nullable=False),
        sa.Column("target_support", sa.String(16), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("iso2", name=op.f("pk_countries")),
        sa.UniqueConstraint("iso3", name=op.f("uq_countries_iso3")),
    )
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("publisher", sa.String(120), nullable=False),
        sa.Column("base_url", sa.String(300), nullable=False),
        sa.Column("docs_url", sa.String(300), nullable=False),
        sa.Column("terms_url", sa.String(300), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=False),
        sa.Column("requires_api_key", sa.Boolean(), nullable=False),
        sa.Column("api_key_env", sa.String(64), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_sources")),
    )
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("rows_upserted", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["data_sources.id"],
            name=op.f("fk_ingestion_runs_source_id_data_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_runs")),
    )
    op.create_index(
        op.f("ix_ingestion_runs_source_id"), "ingestion_runs", ["source_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_runs_source_id"), table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
    op.drop_table("data_sources")
    op.drop_table("countries")
