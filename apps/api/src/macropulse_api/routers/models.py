"""Read-only access to trained model versions and their measured metrics (no training endpoint:
training is a CLI operation on the server, `uv run macropulse train`)."""

from __future__ import annotations

from typing import Annotated

import numpy as np
from fastapi import APIRouter, Path, Query
from sklearn.metrics import precision_recall_curve, roc_curve
from sqlalchemy import select

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.models import ModelMetric, ModelPrediction, ModelVersion
from macropulse_api.schemas import (
    CurvePoint,
    ErrorResponse,
    MetricValue,
    ModelCurves,
    ModelDetail,
    ModelList,
    ModelSummary,
    SplitCurves,
)

router = APIRouter(prefix="/api/models", tags=["models"])

HEADLINE = ("brier", "brier_skill", "log_loss", "roc_auc", "pr_auc")
NOT_TRAINED = "No model has been trained yet. Run `uv run macropulse train` on the server."


def _summary(v: ModelVersion, metrics: list[ModelMetric]) -> dict[str, object]:
    headline: dict[str, dict[str, float | None]] = {}
    for m in metrics:
        if m.segment == "all" and m.metric in HEADLINE:
            headline.setdefault(m.split, {})[m.metric] = m.value
    return {
        "id": v.id,
        "run_id": v.run_id,
        "horizon": v.horizon,
        "model_key": v.model_key,
        "name": v.name,
        "role": v.role,
        "status": v.status,
        "selected": v.selected,
        "unavailable_reason": v.unavailable_reason,
        "created_at": v.created_at,
        "target_version": v.target_version,
        "feature_set_version": v.feature_set_version,
        "training_rows": v.training_rows,
        "training_events": v.training_events,
        "training_last_as_of": v.training_last_as_of,
        "data_snapshot": v.data_snapshot,
        "code_revision": v.code_revision,
        "artifact_available": v.artifact_path is not None,
        "headline": headline,
        "selection_note": v.evaluation.get("selection_note") if v.selected else None,
        "heldout_check": v.evaluation.get("heldout_check") if v.selected else None,
    }


@router.get("", response_model=ModelList, summary="Model versions of the latest (or every) run")
def list_models(
    session: SessionDep,
    run: Annotated[str, Query(pattern=r"^(latest|all)$")] = "latest",
) -> ModelList:
    latest = session.scalar(
        select(ModelVersion.run_id).order_by(ModelVersion.created_at.desc()).limit(1)
    )
    if latest is None:
        return ModelList(run_id=None, items=[], note=NOT_TRAINED)
    query = select(ModelVersion).order_by(
        ModelVersion.created_at.desc(), ModelVersion.horizon, ModelVersion.id
    )
    if run == "latest":
        query = query.where(ModelVersion.run_id == latest)
    versions = session.scalars(query).all()
    metrics = session.scalars(
        select(ModelMetric).where(
            ModelMetric.model_version_id.in_([v.id for v in versions]),
            ModelMetric.segment == "all",
        )
    ).all()
    by_version: dict[str, list[ModelMetric]] = {}
    for m in metrics:
        by_version.setdefault(m.model_version_id, []).append(m)
    items = [ModelSummary(**_summary(v, by_version.get(v.id, []))) for v in versions]
    note = (
        "Metrics are out-of-sample walk-forward results; the held-out years were never used to "
        "choose a model. Probabilities are analytical estimates, not forecasts of certainty."
    )
    return ModelList(run_id=latest, items=items, note=note)


@router.get(
    "/{model_id}/curves",
    response_model=ModelCurves,
    summary="ROC and precision-recall curves from the stored out-of-sample predictions",
    responses={404: {"model": ErrorResponse, "description": "Unknown model version."}},
)
def model_curves(
    session: SessionDep,
    model_id: Annotated[str, Path(pattern=r"^[0-9]{8}T[0-9]{6}Z-h[24]-[a-z_]{2,40}$")],
) -> ModelCurves:
    v = session.get(ModelVersion, model_id)
    if v is None:
        raise ApiError(404, "model_not_found", f"Model version '{model_id}' does not exist.")
    splits: list[SplitCurves] = []
    for split in ("development", "heldout"):
        rows = session.scalars(
            select(ModelPrediction).where(
                ModelPrediction.model_version_id == v.id,
                ModelPrediction.split == split,
                ModelPrediction.label.is_not(None),
            )
        ).all()
        y = np.array([r.label for r in rows], dtype=np.int64)
        p = np.array([r.probability for r in rows], dtype=np.float64)
        events = int(y.sum())
        if not rows or events in (0, len(rows)):
            splits.append(
                SplitCurves(
                    split=split,
                    n=len(rows),
                    events=events,
                    roc=None,
                    pr=None,
                    note="Only one class in this split: curves are undefined.",
                )
            )
            continue
        fpr, tpr, _ = roc_curve(y, p)
        precision, recall, _ = precision_recall_curve(y, p)
        splits.append(
            SplitCurves(
                split=split,
                n=len(rows),
                events=events,
                roc=[CurvePoint(x=float(a), y=float(b)) for a, b in zip(fpr, tpr, strict=True)],
                pr=[
                    CurvePoint(x=float(r), y=float(q))
                    for r, q in zip(recall[::-1], precision[::-1], strict=True)
                ],
                note=None,
            )
        )
    return ModelCurves(model_id=v.id, splits=splits)


@router.get(
    "/{model_id}/metrics",
    response_model=ModelDetail,
    summary="Full metadata, protocol and every measured metric of one model version",
    responses={404: {"model": ErrorResponse, "description": "Unknown model version."}},
)
def model_metrics(
    session: SessionDep,
    model_id: Annotated[str, Path(pattern=r"^[0-9]{8}T[0-9]{6}Z-h[24]-[a-z_]{2,40}$")],
) -> ModelDetail:
    v = session.get(ModelVersion, model_id)
    if v is None:
        raise ApiError(404, "model_not_found", f"Model version '{model_id}' does not exist.")
    metrics = session.scalars(
        select(ModelMetric)
        .where(ModelMetric.model_version_id == v.id)
        .order_by(ModelMetric.split, ModelMetric.segment, ModelMetric.id)
    ).all()
    return ModelDetail(
        **_summary(v, list(metrics)),
        feature_names=v.feature_names,
        params=v.params,
        evaluation=v.evaluation,
        label_cutoff=v.label_cutoff,
        seed=v.seed,
        command=v.command,
        library_versions=v.library_versions,
        coefficients=v.coefficients,
        calibrated_folds=v.calibrated_folds,
        metrics=[
            MetricValue(
                split=m.split,
                segment=m.segment,
                metric=m.metric,
                value=m.value,
                n=m.n,
                events=m.events,
                note=m.note,
                detail=m.detail,
            )
            for m in metrics
        ],
    )
