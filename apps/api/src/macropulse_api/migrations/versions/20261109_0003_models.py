"""Model versions, metrics and predictions.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(80), nullable=False),
        sa.Column("run_id", sa.String(40), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("model_key", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("unavailable_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_version", sa.String(40), nullable=False),
        sa.Column("feature_set_version", sa.String(40), nullable=False),
        sa.Column("feature_names", sa.JSON(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("evaluation", sa.JSON(), nullable=False),
        sa.Column("training_rows", sa.Integer(), nullable=True),
        sa.Column("training_events", sa.Integer(), nullable=True),
        sa.Column("training_last_as_of", sa.String(8), nullable=True),
        sa.Column("label_cutoff", sa.JSON(), nullable=False),
        sa.Column("data_snapshot", sa.String(80), nullable=False),
        sa.Column("data_retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("code_revision", sa.String(60), nullable=True),
        sa.Column("library_versions", sa.JSON(), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column("coefficients", sa.JSON(), nullable=True),
        sa.Column("calibrated_folds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_versions")),
    )
    op.create_index(op.f("ix_model_versions_run_id"), "model_versions", ["run_id"])

    op.create_table(
        "model_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_version_id", sa.String(80), nullable=False),
        sa.Column("split", sa.String(20), nullable=False),
        sa.Column("segment", sa.String(8), nullable=False),
        sa.Column("metric", sa.String(30), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("n", sa.Integer(), nullable=False),
        sa.Column("events", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_model_metrics_model_version_id_model_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_metrics")),
    )
    op.create_index(
        op.f("ix_model_metrics_model_version_id"), "model_metrics", ["model_version_id"]
    )

    op.create_table(
        "model_predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_version_id", sa.String(80), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("as_of", sa.String(8), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("label", sa.Integer(), nullable=True),
        sa.Column("split", sa.String(12), nullable=False),
        sa.Column("fold_year", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_model_predictions_model_version_id_model_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_predictions")),
    )
    op.create_index(
        op.f("ix_model_predictions_model_version_id"), "model_predictions", ["model_version_id"]
    )
    op.create_index(op.f("ix_model_predictions_country"), "model_predictions", ["country"])


def downgrade() -> None:
    op.drop_table("model_predictions")
    op.drop_table("model_metrics")
    op.drop_table("model_versions")
