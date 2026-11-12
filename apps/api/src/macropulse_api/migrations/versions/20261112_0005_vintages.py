"""ALFRED vintages: the full revision history of selected US series.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vintage_series",
        sa.Column("series_id", sa.String(200), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(32),
            sa.ForeignKey("data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("geo", sa.String(8), nullable=False),
        sa.Column("dataset", sa.String(64), nullable=False),
        sa.Column("frequency", sa.String(10), nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rows", sa.Integer(), nullable=False),
        sa.Column("vintages", sa.Integer(), nullable=False),
        sa.Column("first_vintage", sa.Date(), nullable=True),
        sa.Column("last_vintage", sa.Date(), nullable=True),
    )
    op.create_table(
        "vintage_observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "series_id",
            sa.String(200),
            sa.ForeignKey("vintage_series.series_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("realtime_start", sa.Date(), nullable=False),
        sa.Column("realtime_end", sa.Date(), nullable=True),
        sa.UniqueConstraint(
            "series_id", "period", "realtime_start", name="uq_vintage_series_period_start"
        ),
    )
    op.create_index("ix_vintage_observations_series_id", "vintage_observations", ["series_id"])


def downgrade() -> None:
    op.drop_index("ix_vintage_observations_series_id", table_name="vintage_observations")
    op.drop_table("vintage_observations")
    op.drop_table("vintage_series")
