"""Inference round trip: stored observations → as-of snapshot → saved artifact → probability.

Every estimate carries what is needed to judge it: model version and training cut-off, the inputs
and the periods they come from, a local explanation, the model's measured track record and
whether the as-of quarter was inside the training sample (then it is a fit, not a forecast).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse_api.db import as_utc
from macropulse_api.errors import ApiError
from macropulse_api.models import ModelMetric, ModelPrediction, ModelVersion
from macropulse_api.services.training import country_inputs, latest_complete_quarter
from macropulse_economics.periods import period_end, shift
from macropulse_ml.features import FEATURE_NAMES, FEATURES, Snapshot, snapshots
from macropulse_ml.target import LabelStatus, quarter_index, technical_recession_label

TRAIN_HINT = "Run `uv run macropulse train` on the server."
# Fixed, published probability bands (text + colour in the UI, never colour alone).
RISK_BANDS: tuple[tuple[float, str], ...] = (
    (0.15, "low"),
    (0.30, "moderate"),
    (0.50, "elevated"),
    (1.0, "high"),
)
FEATURE_LABELS = dict(FEATURES)

_lock = threading.Lock()
_cache: dict[tuple[str, float], Any] = {}


def risk_band(p: float) -> str:
    for upper, name in RISK_BANDS:
        if p < upper:
            return name
    return RISK_BANDS[-1][1]


def published_version(session: Session, horizon: int) -> ModelVersion:
    run_id = session.scalar(
        select(ModelVersion.run_id).order_by(ModelVersion.created_at.desc()).limit(1)
    )
    if run_id is None:
        raise ApiError(503, "model_not_trained", f"No model has been trained yet. {TRAIN_HINT}")
    v = session.scalars(
        select(ModelVersion).where(
            ModelVersion.run_id == run_id,
            ModelVersion.horizon == horizon,
            ModelVersion.selected.is_(True),
        )
    ).first()
    if v is None:
        raise ApiError(
            503,
            "model_not_trained",
            f"The latest training run has no published model for {horizon} quarters. {TRAIN_HINT}",
        )
    return v


def load_artifact(v: ModelVersion, models_dir: Path) -> Any:
    """Load the saved estimator — only from inside the configured models directory."""
    if not v.artifact_path:
        raise ApiError(
            503,
            "model_artifact_missing",
            f"Model {v.id} was stored without an artifact. {TRAIN_HINT}",
        )
    path = (Path(v.artifact_path) / "model.joblib").resolve()
    if not path.is_relative_to(models_dir.resolve()):
        raise ApiError(
            503,
            "model_artifact_untrusted",
            "The artifact is outside the configured models directory and will not be loaded.",
        )
    if not path.is_file():
        raise ApiError(
            503, "model_artifact_missing", f"Artifact file for {v.id} is missing. {TRAIN_HINT}"
        )
    key = (v.id, path.stat().st_mtime)
    with _lock:
        if key not in _cache:
            _cache[key] = joblib.load(path)
        return _cache[key]


@dataclass
class Explanation:
    method: str
    unit: str
    intercept: float | None
    items: list[dict[str, Any]]
    note: str


def explain(model: Any, x: np.ndarray, summary: dict[str, dict[str, float]]) -> Explanation:
    """Exact additive log-odds contributions for the logistic pipeline; for other models a local
    sensitivity: how the probability changes when one input is set to its training mean."""
    steps = getattr(model, "named_steps", None)
    if steps and "scale" in steps and "model" in steps:
        z = steps["scale"].transform(x)[0]
        coef = steps["model"].coef_[0]
        intercept = float(steps["model"].intercept_[0])
        items = [
            {"feature": name, "contribution": float(c * zi), "standardised_value": float(zi)}
            for name, c, zi in zip(FEATURE_NAMES, coef, z, strict=True)
        ]
        return Explanation(
            method="standardised coefficient x standardised value (exact, additive log-odds)",
            unit="log-odds",
            intercept=intercept,
            items=items,
            note=(
                "Contributions add up, with the intercept, to the log-odds of the estimate. "
                "Zero means the input is at its training mean. SHAP is not installed; for a "
                "linear model this decomposition is exact."
            ),
        )
    p = float(model.predict_proba(x)[0, 1])
    items = []
    for j, name in enumerate(FEATURE_NAMES):
        alt = x.copy()
        alt[0, j] = summary.get(name, {}).get("mean", float(x[0, j]))
        items.append({"feature": name, "contribution": p - float(model.predict_proba(alt)[0, 1])})
    return Explanation(
        method=(
            "local sensitivity: probability minus probability with this input at its training mean"
        ),
        unit="probability",
        intercept=None,
        items=items,
        note=(
            "For tree models without SHAP (not installed) this is a documented fallback. Effects "
            "interact, so they do not add up exactly to the estimate."
        ),
    )


def _track_record(session: Session, v: ModelVersion) -> dict[str, Any]:
    rows = session.scalars(
        select(ModelMetric).where(
            ModelMetric.model_version_id == v.id,
            ModelMetric.segment == "all",
            ModelMetric.metric.in_(["brier", "brier_skill", "brier_reference", "roc_auc"]),
        )
    ).all()
    out: dict[str, Any] = {}
    for m in rows:
        split = out.setdefault(m.split, {"n": m.n, "events": m.events})
        split[m.metric] = m.value
    check = v.evaluation.get("heldout_check") or {}
    out["beats_baseline_heldout"] = (
        check.get("beats_prevalence") if check.get("evaluated") else None
    )
    return out


def snapshot_for(inputs: Any, as_of: str) -> Snapshot | None:
    found = snapshots(inputs, as_of, as_of)
    return found[0] if found else None


def estimate(
    session: Session,
    iso2: str,
    horizon: int,
    as_of: str | None,
    *,
    models_dir: Path,
    today: date | None = None,
) -> dict[str, Any]:
    day = today or datetime.now(UTC).date()
    v = published_version(session, horizon)
    model = load_artifact(v, models_dir)
    if list(v.feature_names) != list(FEATURE_NAMES):
        raise ApiError(
            503,
            "model_incompatible",
            f"Model {v.id} was trained on a different feature set. {TRAIN_HINT}",
        )
    inputs, fetched = country_inputs(session, iso2)

    requested = as_of
    if as_of is not None:
        if period_end(as_of) > day:
            raise ApiError(422, "invalid_as_of", f"As-of quarter {as_of} has not ended yet.")
        snap = snapshot_for(inputs, as_of)
        if snap is None:
            raise ApiError(
                404,
                "features_unavailable",
                f"Not every model input for {iso2} had been published by the end of {as_of} "
                "(or the series start later), so no estimate is made.",
            )
    else:
        as_of = latest_complete_quarter(day)
        snap = snapshot_for(inputs, as_of)
        for _ in range(2):  # the newest quarter may still lack a release; say so, don't guess
            if snap is not None:
                break
            as_of = shift(as_of, -1)
            snap = snapshot_for(inputs, as_of)
        if snap is None:
            raise ApiError(404, "features_unavailable", f"No recent complete input set for {iso2}.")

    x = np.array([[snap.values[name] for name in FEATURE_NAMES]], dtype=np.float64)
    probability = float(model.predict_proba(x)[0, 1])
    summary: dict[str, dict[str, float]] = v.evaluation.get("training_feature_summary") or {}
    expl = explain(model, x, summary)
    for item in expl.items:
        name = item["feature"]
        s = summary.get(name, {})
        value = snap.values[name]
        item |= {
            "label": FEATURE_LABELS[name],
            "value": value,
            "period": snap.used.get(name),
            "training_mean": s.get("mean"),
            "outside_training_range": bool(s) and not (s["min"] <= value <= s["max"]),
            "unusual": bool(s) and not (s["p05"] <= value <= s["p95"]),
        }
    expl.items.sort(key=lambda i: abs(i["contribution"]), reverse=True)

    in_sample = v.training_last_as_of is not None and quarter_index(as_of) <= quarter_index(
        v.training_last_as_of
    )
    label = technical_recession_label(
        inputs.gdp_qoq, as_of, horizon, max(inputs.gdp_qoq, key=quarter_index)
    )
    wf = session.scalars(
        select(ModelPrediction).where(
            ModelPrediction.model_version_id == v.id,
            ModelPrediction.country == iso2,
            ModelPrediction.as_of == as_of,
            ModelPrediction.split != "live",
        )
    ).first()
    stored_live = session.scalars(
        select(ModelPrediction).where(
            ModelPrediction.model_version_id == v.id,
            ModelPrediction.country == iso2,
            ModelPrediction.as_of == as_of,
            ModelPrediction.split == "live",
        )
    ).first()
    base_rate = (
        v.training_events / v.training_rows if v.training_rows and v.training_events else None
    )
    return {
        "country": iso2,
        "horizon": horizon,
        "as_of": as_of,
        "requested_as_of": requested,
        "cutoff": period_end(as_of),
        "probability": probability,
        "band": risk_band(probability),
        "bands": [{"upper": u, "name": n} for u, n in RISK_BANDS],
        "base_rate": base_rate,
        "model": {
            "id": v.id,
            "name": v.name,
            "key": v.model_key,
            "run_id": v.run_id,
            "trained_at": as_utc(v.created_at),
            "training_rows": v.training_rows,
            "training_events": v.training_events,
            "training_last_as_of": v.training_last_as_of,
            "gdp_observed_to": (v.label_cutoff or {}).get(iso2),
            "target_version": v.target_version,
            "feature_set_version": v.feature_set_version,
            "code_revision": v.code_revision,
        },
        "prediction_timestamp": datetime.now(UTC),
        "data_freshness": fetched,
        "inputs_stale": list(snap.stale),
        "explanation": {
            "method": expl.method,
            "unit": expl.unit,
            "intercept": expl.intercept,
            "note": expl.note,
            "items": expl.items,
        },
        "track_record": _track_record(session, v),
        "selection_note": v.evaluation.get("selection_note"),
        "in_sample": in_sample,
        "outcome": {
            "status": label.status.value,
            "label": label.value if label.status is LabelStatus.OBSERVED else None,
            "window": list(label.window),
        },
        "walk_forward_probability": wf.probability if wf else None,
        "walk_forward_split": wf.split if wf else None,
        "stored_estimate": stored_live.probability if stored_live else None,
    }
