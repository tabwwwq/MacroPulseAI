"""`macropulse train`: build the as-of panel from stored observations, run the walk-forward backtest
for each horizon, persist every model's metrics and predictions, and save the selected model.

Inputs go through the same loader as the dashboards (`series_data.load_indicator`), so a model sees
exactly the stored official series a user can inspect — never a different copy.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import joblib
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from macropulse_api.db import as_utc
from macropulse_api.errors import ApiError
from macropulse_api.models import ModelMetric, ModelPrediction, ModelVersion, Observation
from macropulse_api.services.series_data import load_indicator, resolve_indicator
from macropulse_economics import COUNTRIES
from macropulse_economics.periods import period_end, quarter_of, shift
from macropulse_ml import FEATURE_SET_VERSION, TARGET_VERSION
from macropulse_ml.backtest import DEV_END_YEAR, FIRST_TEST_YEAR, SPLITS, HorizonResult, run_horizon
from macropulse_ml.features import (
    EXCLUDED_INPUTS,
    FEATURES,
    LAG_DAYS,
    MAX_EXTRA_MONTHS,
    CountryInputs,
)
from macropulse_ml.metrics import CALIBRATION_EDGES, THRESHOLD, MetricSet
from macropulse_ml.panel import Panel, build_panel
from macropulse_ml.target import HORIZONS

FIRST_AS_OF = "1955-Q1"
INPUT_INDICATORS: tuple[str, ...] = (
    "real_gdp_qoq",
    "real_gdp_yoy",
    "inflation_yoy",
    "unemployment_rate",
    "policy_rate",
    "bond_yield_10y",
    "short_rate_3m",
)


@dataclass
class TrainReport:
    run_id: str
    panel: Panel
    horizons: dict[int, HorizonResult]
    skipped: dict[str, str]
    data_snapshot: str
    artifact_dir: Path | None
    version_ids: list[str] = field(default_factory=list)


def latest_complete_quarter(today: date) -> str:
    """The newest quarter that has fully ended by `today`."""
    current = quarter_of(today)
    return current if period_end(current) <= today else shift(current, -1)


def country_inputs(session: Session, iso2: str) -> tuple[CountryInputs, datetime | None]:
    """Model inputs for one country from stored observations, and the latest fetch time behind
    them. Raises ApiError (404/503) when an input is not published or not synced."""
    series: dict[str, dict[str, float]] = {}
    event_dated = False
    fetched: list[datetime] = []
    for ind_id in INPUT_INDICATORS:
        data = load_indicator(session, iso2, resolve_indicator(ind_id))
        series[ind_id] = dict(data.points)
        stamp = as_utc(data.latest_row.retrieved_at)
        if stamp is not None:
            fetched.append(stamp)
        if ind_id == "policy_rate":
            event_dated = data.mapping.native_frequency.value == "event"
    inputs = CountryInputs(
        country=iso2,
        gdp_qoq=series["real_gdp_qoq"],
        gdp_yoy=series["real_gdp_yoy"],
        inflation=series["inflation_yoy"],
        unemployment=series["unemployment_rate"],
        policy_rate=series["policy_rate"],
        policy_rate_event_dated=event_dated,
        bond_yield=series["bond_yield_10y"],
        short_rate=series["short_rate_3m"],
    )
    return inputs, max(fetched) if fetched else None


def load_inputs(session: Session) -> tuple[list[CountryInputs], dict[str, str], str]:
    """Country inputs from stored observations, the countries skipped (with reason) and a hash of
    exactly the values used (dataset snapshot)."""
    inputs: list[CountryInputs] = []
    skipped: dict[str, str] = {}
    digest = hashlib.sha256()
    for country in COUNTRIES:
        try:
            c, _ = country_inputs(session, country.iso2)
        except ApiError as exc:
            skipped[country.iso2] = f"{exc.code}: {exc.message}"
            continue
        named = {
            "real_gdp_qoq": c.gdp_qoq,
            "real_gdp_yoy": c.gdp_yoy,
            "inflation_yoy": c.inflation,
            "unemployment_rate": c.unemployment,
            "policy_rate": c.policy_rate,
            "bond_yield_10y": c.bond_yield,
            "short_rate_3m": c.short_rate,
        }
        for ind_id in INPUT_INDICATORS:
            for period, value in sorted(named[ind_id].items()):
                digest.update(f"{country.iso2}|{ind_id}|{period}|{value!r}\n".encode())
        inputs.append(c)
    return inputs, skipped, f"sha256:{digest.hexdigest()[:32]}"


def library_versions() -> dict[str, str]:
    out = {"python": platform.python_version()}
    for pkg in ("numpy", "scikit-learn", "scipy", "joblib", "macropulse-ml"):
        try:
            out[pkg] = version(pkg)
        except Exception:  # pragma: no cover - reported, never fatal
            out[pkg] = "unknown"
    return out


def heldout_check(result: HorizonResult) -> dict[str, Any]:
    """After selection: does the published model beat the prevalence baseline on held-out data?
    This is reported (and shown to users) — it never changes which model is published."""
    if result.selected is None:
        return {"evaluated": False}
    m = result.results[result.selected].metrics.get("heldout")
    if m is None or not m.n:
        return {"evaluated": False, "reason": "No labelled held-out observations."}
    skill = m.values.get("brier_skill")
    return {
        "evaluated": True,
        "n": m.n,
        "events": m.events,
        "brier": m.values.get("brier"),
        "brier_reference": m.values.get("brier_reference"),
        "brier_skill": skill,
        "beats_prevalence": skill is not None and skill > 0,
    }


def protocol(horizon: int, result: HorizonResult) -> dict[str, Any]:
    return {
        "heldout_check": heldout_check(result),
        "training_feature_summary": result.feature_summary,
        # Covariance of the training features (order = `features`), for joint OOD checks.
        "training_feature_covariance": result.feature_covariance,
        "method": "expanding-window walk-forward, one fold per calendar year, pooled countries",
        "purge": f"training labels must end before the first test quarter (t + {horizon} <= s - 1)",
        "first_test_year": FIRST_TEST_YEAR,
        "development_years": f"{FIRST_TEST_YEAR}-{DEV_END_YEAR}",
        "heldout_years": f"{DEV_END_YEAR + 1}-",
        "selection": (
            "lowest development Brier among candidates, only if it beats the prevalence "
            "baseline; otherwise the best baseline is published. Held-out never used."
        ),
        "selection_note": result.selection_note,
        "threshold": THRESHOLD,
        "calibration_bins": list(CALIBRATION_EDGES),
        "folds": [
            {"year": f.year, "train_rows": len(f.train), "test_rows": len(f.test)}
            for f in result.folds
        ],
        "skipped_folds": result.notes,
        "publication_lag_days": LAG_DAYS,
        "max_extra_stale_months": MAX_EXTRA_MONTHS,
        "excluded_inputs": EXCLUDED_INPUTS,
        "features": dict(FEATURES),
        "labels": "latest revised GDP; censored and missing windows excluded",
    }


def _metric_rows(version_id: str, split: str, segment: str, m: MetricSet) -> list[ModelMetric]:
    rows = [
        ModelMetric(
            model_version_id=version_id,
            split=split,
            segment=segment,
            metric=name,
            value=value,
            n=m.n,
            events=m.events,
            note=m.notes.get(name),
        )
        for name, value in m.values.items()
    ]
    if segment == "all" and m.n:
        rows.append(
            ModelMetric(
                model_version_id=version_id,
                split=split,
                segment=segment,
                metric="calibration",
                value=None,
                n=m.n,
                events=m.events,
                detail=m.calibration,
            )
        )
        rows.append(
            ModelMetric(
                model_version_id=version_id,
                split=split,
                segment=segment,
                metric="confusion",
                value=None,
                n=m.n,
                events=m.events,
                detail=m.confusion,
            )
        )
    if not m.n:
        rows.append(
            ModelMetric(
                model_version_id=version_id,
                split=split,
                segment=segment,
                metric="n",
                value=0,
                n=0,
                events=0,
                note=m.notes.get("all"),
            )
        )
    return rows


def train(
    factory: sessionmaker[Session],
    *,
    horizons: tuple[int, ...] = HORIZONS,
    seed: int = 42,
    artifacts_root: Path | None = None,
    command: str = "macropulse train",
    code_revision: str | None = None,
    today: date | None = None,
) -> TrainReport:
    now = datetime.now(UTC)
    day = today or now.date()
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    with factory() as session:
        inputs, skipped, snapshot = load_inputs(session)
        retrieved = session.scalar(select(func.max(Observation.retrieved_at)))
    if not inputs:
        raise ApiError(503, "data_not_synced", "No country has the inputs needed for training.")

    last_as_of = latest_complete_quarter(day)
    panel = build_panel(inputs, FIRST_AS_OF, last_as_of, horizons)
    results = {h: run_horizon(panel, h, seed, int(last_as_of[:4])) for h in horizons}
    report = TrainReport(run_id, panel, results, skipped, snapshot, None)
    libs = library_versions()

    artifact_dir = artifacts_root / run_id if artifacts_root else None
    with factory() as session:
        for h, result in results.items():
            for key, res in result.results.items():
                vid = f"{run_id}-h{h}-{key}"
                is_selected = key == result.selected
                path: str | None = None
                if is_selected and artifact_dir is not None and result.final_model is not None:
                    target = artifact_dir / f"h{h}"
                    target.mkdir(parents=True, exist_ok=True)
                    joblib.dump(result.final_model, target / "model.joblib")
                    path = str(target)
                version = ModelVersion(
                    id=vid,
                    run_id=run_id,
                    horizon=h,
                    model_key=key,
                    name=res.spec.name,
                    role=res.spec.role,
                    status="evaluated" if res.available else "unavailable",
                    selected=is_selected,
                    unavailable_reason=res.unavailable_reason,
                    created_at=now,
                    target_version=TARGET_VERSION,
                    feature_set_version=FEATURE_SET_VERSION,
                    feature_names=list(panel.feature_names),
                    params={**res.spec.params, "seed": seed},
                    evaluation=protocol(h, result),
                    training_rows=result.final_n if is_selected else None,
                    training_events=result.final_events if is_selected else None,
                    training_last_as_of=result.final_last_as_of if is_selected else None,
                    label_cutoff=panel.last_observed,
                    data_snapshot=snapshot,
                    data_retrieved_at=retrieved,
                    seed=seed,
                    command=command,
                    code_revision=code_revision,
                    library_versions=libs,
                    artifact_path=path,
                    coefficients=result.coefficients if key == "logistic" else None,
                    calibrated_folds=res.calibrated_folds,
                )
                session.add(version)
                session.flush()
                for split in SPLITS:
                    if split in res.metrics:
                        session.add_all(_metric_rows(vid, split, "all", res.metrics[split]))
                        for country, m in res.by_country.get(split, {}).items():
                            session.add_all(_metric_rows(vid, split, country, m))
                preds = list(res.predictions) + (list(result.live) if is_selected else [])
                session.add_all(
                    ModelPrediction(
                        model_version_id=vid,
                        country=p.country,
                        as_of=p.as_of,
                        horizon=h,
                        probability=p.probability,
                        label=p.label,
                        split=p.split,
                        fold_year=p.fold_year,
                    )
                    for p in preds
                )
                report.version_ids.append(vid)
                if path is not None:
                    _write_metadata(Path(path), version, result, panel)
        session.commit()
    report.artifact_dir = artifact_dir
    return report


def _write_metadata(path: Path, v: ModelVersion, result: HorizonResult, panel: Panel) -> None:
    meta = {
        "model_version": v.id,
        "horizon": v.horizon,
        "model": v.model_key,
        "target_version": v.target_version,
        "feature_set_version": v.feature_set_version,
        "features": v.feature_names,
        "training_rows": v.training_rows,
        "training_events": v.training_events,
        "training_last_as_of": v.training_last_as_of,
        "label_cutoff": v.label_cutoff,
        "data_snapshot": v.data_snapshot,
        "seed": v.seed,
        "command": v.command,
        "code_revision": v.code_revision,
        "library_versions": v.library_versions,
        "evaluation": v.evaluation,
        "events_in_data": {c: runs for c, runs in panel.events.items()},
        "live": [
            {"country": p.country, "as_of": p.as_of, "probability": p.probability}
            for p in result.live
        ],
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }
    (path / "metadata.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
