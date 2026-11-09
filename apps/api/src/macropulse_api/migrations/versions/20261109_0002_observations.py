"""Observations and data-quality checks.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("series_id", sa.String(200), nullable=False),
        sa.Column("source_id", sa.String(32), nullable=False),
        sa.Column("geo", sa.String(8), nullable=False),
        sa.Column("dataset", sa.String(64), nullable=False),
        sa.Column("series_key", sa.String(200), nullable=False),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(10), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("adjustment", sa.String(64), nullable=True),
        sa.Column("obs_status", sa.String(16), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_updated_at", sa.String(40), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["data_sources.id"],
            name=op.f("fk_observations_source_id_data_sources"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_runs.id"],
            name=op.f("fk_observations_ingestion_run_id_ingestion_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observations")),
        sa.UniqueConstraint("series_id", "period", name="uq_observations_series_period"),
    )
    op.create_index(op.f("ix_observations_series_id"), "observations", ["series_id"])
    op.create_index(op.f("ix_observations_geo"), "observations", ["geo"])
    op.create_index(op.f("ix_observations_ingestion_run_id"), "observations", ["ingestion_run_id"])

    op.create_table(
        "quality_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("series_id", sa.String(200), nullable=False),
        sa.Column("rule", sa.String(40), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_runs.id"],
            name=op.f("fk_quality_checks_ingestion_run_id_ingestion_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_checks")),
    )
    op.create_index(
        op.f("ix_quality_checks_ingestion_run_id"), "quality_checks", ["ingestion_run_id"]
    )
    op.create_index(op.f("ix_quality_checks_series_id"), "quality_checks", ["series_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_quality_checks_series_id"), table_name="quality_checks")
    op.drop_index(op.f("ix_quality_checks_ingestion_run_id"), table_name="quality_checks")
    op.drop_table("quality_checks")
    op.drop_index(op.f("ix_observations_ingestion_run_id"), table_name="observations")
    op.drop_index(op.f("ix_observations_geo"), table_name="observations")
    op.drop_index(op.f("ix_observations_series_id"), table_name="observations")
    op.drop_table("observations")
