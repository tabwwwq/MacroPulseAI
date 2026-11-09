"""Walk-forward backtest, model selection and final fit for one horizon.

Protocol (fixed before looking at results):
- Expanding window, one fold per calendar year from FIRST_TEST_YEAR; horizon purge (see splits).
- Every model is refitted in every fold on training rows only (scalers included, via pipelines).
- Out-of-sample predictions for 2000-2014 form the *development* backtest; 2015 onwards is the
  *held-out* backtest. The published model is the candidate with the lowest development Brier
  score if it beats the prevalence baseline there; otherwise the best baseline is published and
  the selection note says so. Held-out results never influence the choice.
- The selected model is refitted on all labelled rows; its estimate for each country's latest
  as-of quarter is the current (unlabelled) prediction.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial

import numpy as np
from numpy.typing import NDArray

from macropulse_ml.metrics import MetricSet, evaluate
from macropulse_ml.models import (
    SPECS,
    Classifier,
    ModelSpec,
    PlattCalibrated,
    boosted,
    logistic,
    make,
    xgboost_available,
)
from macropulse_ml.panel import Panel
from macropulse_ml.splits import Fold, walk_forward

FIRST_TEST_YEAR = 2000
DEV_END_YEAR = 2014
SPLITS = ("development", "heldout")


@dataclass(frozen=True)
class Prediction:
    country: str
    as_of: str
    probability: float
    label: int | None
    fold_year: int | None
    split: str  # development | heldout | unlabelled | live


@dataclass
class ModelResult:
    spec: ModelSpec
    available: bool
    unavailable_reason: str | None = None
    predictions: list[Prediction] = field(default_factory=list)
    metrics: dict[str, MetricSet] = field(default_factory=dict)
    by_country: dict[str, dict[str, MetricSet]] = field(default_factory=dict)
    calibrated_folds: int | None = None


@dataclass
class HorizonResult:
    horizon: int
    folds: list[Fold]
    notes: list[str]
    results: dict[str, ModelResult]
    selected: str | None
    final_model: object | None = None
    final_n: int = 0
    final_events: int = 0
    final_last_as_of: str | None = None
    live: list[Prediction] = field(default_factory=list)
    coefficients: dict[str, float] = field(default_factory=dict)
    selection_note: str = ""


def _fit(
    spec: ModelSpec, seed: int, panel: Panel, idx: list[int], horizon: int
) -> tuple[Classifier, bool]:
    x, y = panel.matrix(idx), panel.target(idx, horizon)
    if spec.key == "hist_gbm_platt":
        q = np.array([panel.rows[i].q for i in idx], dtype=np.int64)
        model = PlattCalibrated(partial(boosted, seed)).fit_temporal(x, y, q, horizon)
        return model, model.calibrated
    return make(spec.key, seed).fit(x, y), False


def _predict(model: Classifier, panel: Panel, idx: list[int]) -> NDArray[np.float64]:
    proba = np.asarray(model.predict_proba(panel.matrix(idx)), dtype=np.float64)
    return proba[:, 1]


def _split(year: int, label: int | None) -> str:
    if label is None:
        return "unlabelled"
    return "development" if year <= DEV_END_YEAR else "heldout"


def run_horizon(panel: Panel, horizon: int, seed: int, last_year: int) -> HorizonResult:
    folds, notes = walk_forward(panel, horizon, FIRST_TEST_YEAR, last_year)
    results: dict[str, ModelResult] = {}
    for spec in SPECS:
        if spec.key == "xgboost" and not xgboost_available():
            results[spec.key] = ModelResult(
                spec, False, "xgboost is not installed (optional extra: uv sync --extra xgboost)."
            )
            continue
        res = ModelResult(spec, True)
        calibrated = 0
        for fold in folds:
            model, was_calibrated = _fit(spec, seed, panel, fold.train, horizon)
            calibrated += int(was_calibrated)
            probs = _predict(model, panel, fold.test)
            for i, p in zip(fold.test, probs, strict=True):
                row = panel.rows[i]
                label = row.labels[horizon]
                res.predictions.append(
                    Prediction(
                        row.country, row.as_of, float(p), label, fold.year, _split(fold.year, label)
                    )
                )
        if spec.calibrated:
            res.calibrated_folds = calibrated
        results[spec.key] = res

    _score(results)
    selected, note = select(results)
    out = HorizonResult(horizon, folds, notes, results, selected, selection_note=note)
    _final_fit(out, panel, seed)
    return out


def _dev_brier(r: ModelResult) -> float:
    m = r.metrics.get("development")
    value = m.values.get("brier") if m else None
    return value if value is not None else float("inf")


def select(results: dict[str, ModelResult]) -> tuple[str | None, str]:
    """The published model: the candidate with the lowest development Brier score — but only if it
    beats the prevalence baseline there. Otherwise the best *baseline* is published and the note
    says so. Held-out results are never consulted."""
    evaluated = [r for r in results.values() if r.available and "development" in r.metrics]
    candidates = [r for r in evaluated if r.spec.role == "candidate"]
    baselines = [r for r in evaluated if r.spec.role == "baseline"]
    if not baselines:
        return None, "No baseline could be evaluated."
    prevalence = _dev_brier(results["prevalence"])
    best_candidate = min(candidates, key=_dev_brier, default=None)
    if best_candidate is not None and _dev_brier(best_candidate) < prevalence:
        return best_candidate.spec.key, (
            f"{best_candidate.spec.name} has the lowest development Brier score "
            f"({_dev_brier(best_candidate):.4f}) and beats the prevalence baseline "
            f"({prevalence:.4f})."
        )
    best_baseline = min(baselines, key=_dev_brier)
    lead = (
        f"No candidate beats the prevalence baseline on the development backtest "
        f"(best candidate {best_candidate.spec.name}: {_dev_brier(best_candidate):.4f} vs "
        f"{prevalence:.4f})."
        if best_candidate is not None
        else "No candidate model could be evaluated."
    )
    return (
        best_baseline.spec.key,
        f"{lead} The published estimate is the {best_baseline.spec.name}.",
    )


def _score(results: dict[str, ModelResult]) -> None:
    """Metrics per split and per country, with the prevalence baseline as the Brier reference."""
    reference = {
        (p.country, p.as_of): p.probability
        for p in results["prevalence"].predictions
        if p.label is not None
    }
    for res in results.values():
        if not res.available:
            continue
        grouped: dict[str, list[Prediction]] = defaultdict(list)
        for p in res.predictions:
            if p.label is not None:
                grouped[p.split].append(p)
        for split in SPLITS:
            preds = grouped.get(split, [])
            res.metrics[split] = _metric_set(preds, reference)
            per_country: dict[str, list[Prediction]] = defaultdict(list)
            for p in preds:
                per_country[p.country].append(p)
            res.by_country[split] = {
                c: _metric_set(ps, reference) for c, ps in sorted(per_country.items())
            }


def _metric_set(preds: list[Prediction], reference: dict[tuple[str, str], float]) -> MetricSet:
    y = np.array([p.label for p in preds], dtype=np.int64)
    prob = np.array([p.probability for p in preds], dtype=np.float64)
    ref = np.array([reference[(p.country, p.as_of)] for p in preds], dtype=np.float64)
    return evaluate(y, prob, ref)


def _final_fit(out: HorizonResult, panel: Panel, seed: int) -> None:
    labelled = panel.labelled(out.horizon)
    if not labelled:
        return
    out.final_n = len(labelled)
    out.final_events = int(panel.target(labelled, out.horizon).sum())
    out.final_last_as_of = panel.rows[max(labelled, key=lambda i: panel.rows[i].q)].as_of

    # Standardised logistic coefficients: an honest, inspectable explanation of the linear model.
    lr = logistic(seed).fit(panel.matrix(labelled), panel.target(labelled, out.horizon))
    coefs = lr.named_steps["model"].coef_[0]
    out.coefficients = {n: float(c) for n, c in zip(panel.feature_names, coefs, strict=True)}

    if out.selected is None:
        return
    spec = next(s for s in SPECS if s.key == out.selected)
    model, _ = _fit(spec, seed, panel, labelled, out.horizon)
    out.final_model = model
    latest: dict[str, int] = {}
    for i, row in enumerate(panel.rows):
        if row.country not in latest or row.q > panel.rows[latest[row.country]].q:
            latest[row.country] = i
    idx = sorted(latest.values(), key=lambda i: panel.rows[i].country)
    probs = _predict(model, panel, idx)
    out.live = [
        Prediction(
            panel.rows[i].country,
            panel.rows[i].as_of,
            float(p),
            panel.rows[i].labels[out.horizon],
            None,
            "live",
        )
        for i, p in zip(idx, probs, strict=True)
    ]
