"""Scenario lab: exploratory sensitivity of the published recession model to bounded input shocks.

This is model sensitivity analysis, not a causal economic simulation: shocks move the model's
inputs mechanically (rules below) and the response shows how the *model's* probability changes.
Combinations far from anything in the training data are flagged, per input and jointly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import chi2
from sqlalchemy.orm import Session

from macropulse_api.errors import ApiError
from macropulse_api.services import inference
from macropulse_api.services.training import country_inputs, latest_complete_quarter
from macropulse_economics.periods import period_end
from macropulse_ml.features import FEATURE_NAMES, FEATURES

DISCLAIMER = "Exploratory model sensitivity analysis, not a causal economic simulation."
LABELS = dict(FEATURES)


@dataclass(frozen=True)
class Shock:
    key: str
    label: str
    unit: str
    minimum: float
    maximum: float
    step: float
    effect: str  # how the shock is mapped onto model inputs


SHOCKS: tuple[Shock, ...] = (
    Shock(
        "gdp",
        "Real GDP growth, latest quarter",
        "pp",
        -5.0,
        5.0,
        0.1,
        "Adds the shock to latest q/q growth and to y/y growth; recounts negative quarters.",
    ),
    Shock(
        "inflation",
        "Inflation",
        "pp",
        -5.0,
        5.0,
        0.1,
        "Adds the shock to the inflation level and to its six-month change.",
    ),
    Shock(
        "unemployment",
        "Unemployment rate",
        "pp",
        -4.0,
        4.0,
        0.1,
        "Adds the shock to the unemployment level and to its six-month change.",
    ),
    Shock(
        "policy_rate",
        "Policy rate",
        "pp",
        -4.0,
        4.0,
        0.05,
        "Adds the shock to the policy rate and its four-quarter change; the short end of the curve "
        "moves with it, so the term spread falls by the same amount.",
    ),
    Shock(
        "long_rate",
        "10-year government yield",
        "pp",
        -3.0,
        3.0,
        0.05,
        "Adds the shock to the term spread (10-year minus 3-month).",
    ),
)
SHOCK_INDEX = {s.key: s for s in SHOCKS}


def apply_shocks(values: dict[str, float], shocks: dict[str, float]) -> dict[str, float]:
    """Mechanical mapping of shocks onto model inputs (documented in `SHOCKS`)."""
    out = dict(values)
    g = shocks.get("gdp", 0.0)
    if g:
        before = out["gdp_qoq_1"]
        out["gdp_qoq_1"] = before + g
        out["gdp_yoy_1"] += g
        out["gdp_neg_4"] += float(out["gdp_qoq_1"] < 0) - float(before < 0)
    i = shocks.get("inflation", 0.0)
    out["infl_yoy"] += i
    out["infl_chg_6m"] += i
    u = shocks.get("unemployment", 0.0)
    out["unemp"] += u
    out["unemp_chg_6m"] += u
    r = shocks.get("policy_rate", 0.0)
    out["rate"] += r
    out["rate_chg_4q"] += r
    out["term_spread"] += shocks.get("long_rate", 0.0) - r
    return out


def _mahalanobis(x: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
    inv = np.linalg.pinv(cov)
    d = x - mean
    return float(d @ inv @ d)


def joint_check(
    x0: np.ndarray, x1: np.ndarray, summary: dict[str, dict[str, float]], cov: Any
) -> dict[str, Any]:
    """Squared Mahalanobis distance of baseline and scenario inputs from the training mean, with
    a chi-square(k) 99 % threshold as the 'unusual combination' line."""
    if not cov or not summary:
        return {"available": False}
    mean = np.array([summary[n]["mean"] for n in FEATURE_NAMES])
    cov_m = np.array(cov, dtype=np.float64)
    d0 = _mahalanobis(x0, mean, cov_m)
    d1 = _mahalanobis(x1, mean, cov_m)
    k = len(FEATURE_NAMES)
    threshold = float(chi2.ppf(0.99, k))
    return {
        "available": True,
        "baseline_distance": d0,
        "scenario_distance": d1,
        "threshold_99": threshold,
        "scenario_tail_probability": float(chi2.sf(d1, k)),
        "unusual_combination": d1 > threshold,
    }


def evaluate(
    session: Session,
    iso2: str,
    horizon: int,
    as_of: str | None,
    shocks: dict[str, float],
    *,
    models_dir: Path,
    today: date | None = None,
) -> dict[str, Any]:
    for key, value in shocks.items():
        spec = SHOCK_INDEX.get(key)
        if spec is None or not spec.minimum <= value <= spec.maximum:
            raise ApiError(422, "invalid_shock", f"Shock '{key}' is unknown or out of bounds.")
    day = today or datetime.now(UTC).date()
    v = inference.published_version(session, horizon)
    model = inference.load_artifact(v, models_dir)
    if list(v.feature_names) != list(FEATURE_NAMES):
        raise ApiError(503, "model_incompatible", f"Model {v.id} uses another feature set.")
    inputs, _ = country_inputs(session, iso2)
    if as_of is not None and period_end(as_of) > day:
        raise ApiError(422, "invalid_as_of", f"As-of quarter {as_of} has not ended yet.")
    quarter = as_of or latest_complete_quarter(day)
    snap = inference.snapshot_for(inputs, quarter)
    if snap is None:
        raise ApiError(
            404, "features_unavailable", f"No complete input set for {iso2} at {quarter}."
        )

    base_values = {n: snap.values[n] for n in FEATURE_NAMES}
    scen_values = apply_shocks(base_values, shocks)
    x0 = np.array([[base_values[n] for n in FEATURE_NAMES]], dtype=np.float64)
    x1 = np.array([[scen_values[n] for n in FEATURE_NAMES]], dtype=np.float64)
    p0 = float(model.predict_proba(x0)[0, 1])
    p1 = float(model.predict_proba(x1)[0, 1])
    summary: dict[str, dict[str, float]] = v.evaluation.get("training_feature_summary") or {}
    e0 = inference.explain(model, x0, summary)
    e1 = inference.explain(model, x1, summary)
    c0 = {i["feature"]: i["contribution"] for i in e0.items}
    c1 = {i["feature"]: i["contribution"] for i in e1.items}

    inputs_out = []
    for name in FEATURE_NAMES:
        s = summary.get(name, {})
        val = scen_values[name]
        inputs_out.append(
            {
                "feature": name,
                "label": LABELS[name],
                "baseline": base_values[name],
                "scenario": val,
                "changed": abs(val - base_values[name]) > 1e-12,
                "training_min": s.get("min"),
                "training_max": s.get("max"),
                "outside_training_range": bool(s) and not (s["min"] <= val <= s["max"]),
                "unusual": bool(s) and not (s["p05"] <= val <= s["p95"]),
            }
        )
    contributions = sorted(
        (
            {
                "feature": n,
                "label": LABELS[n],
                "baseline": c0[n],
                "scenario": c1[n],
                "delta": c1[n] - c0[n],
            }
            for n in FEATURE_NAMES
        ),
        key=lambda c: abs(c["delta"]),
        reverse=True,
    )

    warnings: list[str] = []
    outside = [str(i["label"]) for i in inputs_out if i["outside_training_range"]]
    if outside:
        warnings.append(
            "Outside anything seen in training: "
            + "; ".join(outside)
            + ". The model is extrapolating."
        )
    joint = joint_check(x0[0], x1[0], summary, v.evaluation.get("training_feature_covariance"))
    if not joint["available"]:
        warnings.append("Joint plausibility check unavailable: retrain to store the covariance.")
    elif joint["unusual_combination"]:
        warnings.append(
            "Unusual combination of inputs: farther from the training data than 99 % of a "
            "normal approximation would place it (squared Mahalanobis distance "
            f"{joint['scenario_distance']:.1f} vs {joint['threshold_99']:.1f}). "
            "Treat the result as unsupported."
        )
    if v.evaluation.get("heldout_check", {}).get("beats_prevalence") is False:
        warnings.append(
            "The underlying model does not beat the base rate on the 2015+ held-out years."
        )

    return {
        "country": iso2,
        "horizon": horizon,
        "as_of": quarter,
        "model": {"id": v.id, "name": v.name, "run_id": v.run_id},
        "shocks": {s.key: shocks.get(s.key, 0.0) for s in SHOCKS},
        "baseline": {"probability": p0, "band": inference.risk_band(p0)},
        "scenario": {"probability": p1, "band": inference.risk_band(p1)},
        "delta": p1 - p0,
        "explanation_unit": e0.unit,
        "explanation_method": e0.method,
        "inputs": inputs_out,
        "contributions": contributions,
        "joint_check": joint,
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
        "computed_at": datetime.now(UTC),
    }
