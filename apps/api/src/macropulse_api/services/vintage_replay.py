"""US replay with the figures as first published (ALFRED vintages).

For a past as-of quarter, the walk-forward fold model of that year is fitted again exactly as the
backtest did and must reproduce the stored estimate on today's revised inputs. Only then is it
scored a second time on inputs rebuilt from the vintage valid on the as-of cut-off: real GDP, CPI
inflation and unemployment as published that day; market rates (policy rate, 10-year yield,
3-month bill) are not revised and come from the stored series. Same publication lags as always.

What this does NOT change: the fold model was trained on today's revised history and labels, and
the outcome is judged on today's GDP. It answers "what would this model have said with the data on
the table then", not "what did anyone forecast".
"""

from __future__ import annotations

import threading
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.orm import Session

from macropulse_api.errors import ApiError
from macropulse_api.models import ModelPrediction, ModelVersion
from macropulse_api.services import inference
from macropulse_api.services.replay import LABELS, OUT_OF_SAMPLE
from macropulse_api.services.training import (
    FIRST_AS_OF,
    country_inputs,
    latest_complete_quarter,
    load_inputs,
)
from macropulse_api.services.vintages import load_vintages, vintage_requests
from macropulse_economics.connectors.alfred import VintageObservation
from macropulse_economics.indicators import mappings_for
from macropulse_economics.periods import period_end
from macropulse_economics.series import request_for
from macropulse_economics.transforms import transform_for
from macropulse_economics.vintages import vintage_series
from macropulse_ml.features import FEATURE_NAMES, CountryInputs, Snapshot
from macropulse_ml.models import Classifier
from macropulse_ml.panel import build_panel
from macropulse_ml.refit import fold_model, predict_one

COUNTRY = "US"
# A re-fitted fold model must reproduce the stored walk-forward probability to this tolerance.
REPRODUCE_TOLERANCE = 1e-9
# Features rebuilt from vintages; the rest come from series that are not revised.
VINTAGE_FEATURES = {
    "gdp_qoq_1",
    "gdp_qoq_2",
    "gdp_yoy_1",
    "gdp_neg_4",
    "infl_yoy",
    "infl_chg_6m",
    "unemp",
    "unemp_chg_6m",
}

_cache: dict[tuple[str, int], Classifier | None] = {}
_lock = threading.Lock()


def _stored_row(session: Session, v: ModelVersion, as_of: str) -> ModelPrediction | None:
    return (
        session.query(ModelPrediction)
        .filter(
            ModelPrediction.model_version_id == v.id,
            ModelPrediction.country == COUNTRY,
            ModelPrediction.as_of == as_of,
            ModelPrediction.split.in_(OUT_OF_SAMPLE),
        )
        .one_or_none()
    )


def _vintage_rows(session: Session) -> dict[str, list[VintageObservation]]:
    rows = {r.dataset: load_vintages(session, r.series_id) for r in vintage_requests()}
    missing = sorted(name for name, found in rows.items() if not found)
    if missing:
        raise ApiError(
            503,
            "vintages_not_synced",
            "No ALFRED vintages are stored for "
            + ", ".join(missing)
            + ". Run `uv run macropulse vintages-sync` on the server (needs FRED_API_KEY).",
        )
    return rows


def vintage_inputs(
    base: CountryInputs, rows: dict[str, list[VintageObservation]], on: date
) -> CountryInputs:
    """US inputs with GDP, CPI and unemployment exactly as published on `on`, derived with the
    same transforms as the stored series (growth from levels of that one vintage)."""
    mappings = mappings_for(COUNTRY)

    def series(indicator: str) -> dict[str, float]:
        mapping = mappings[indicator]
        transform = transform_for(indicator, mapping.source_id)
        return vintage_series(rows[request_for(mapping).dataset], on, transform)

    return replace(
        base,
        gdp_qoq=series("real_gdp_qoq"),
        gdp_yoy=series("real_gdp_yoy"),
        inflation=series("inflation_yoy"),
        unemployment=series("unemployment_rate"),
    )


def _fold_model(session: Session, v: ModelVersion, fold_year: int) -> Classifier | None:
    key = (v.id, fold_year)
    with _lock:
        if key in _cache:
            return _cache[key]
    inputs, _, _ = load_inputs(session)
    first_as_of = str(v.evaluation.get("panel_first_as_of") or FIRST_AS_OF)
    last_as_of = str(
        v.evaluation.get("panel_last_as_of") or latest_complete_quarter(v.created_at.date())
    )
    panel = build_panel(inputs, first_as_of, last_as_of, (v.horizon,))
    model = fold_model(panel, v.horizon, v.model_key, int(v.params.get("seed", 42)), fold_year)
    with _lock:
        _cache[key] = model
    return model


def _compare(revised: Snapshot, vintage: Snapshot) -> list[dict[str, Any]]:
    out = []
    for name in FEATURE_NAMES:
        r, f = revised.values[name], vintage.values[name]
        out.append(
            {
                "feature": name,
                "label": LABELS.get(name, name),
                "from_vintage": name in VINTAGE_FEATURES,
                "revised_value": r,
                "revised_period": revised.used.get(name),
                "vintage_value": f,
                "vintage_period": vintage.used.get(name),
                "difference": f - r,
            }
        )
    return out


def vintage_replay(session: Session, horizon: int, as_of: str) -> dict[str, Any]:
    v = inference.published_version(session, horizon)
    row = _stored_row(session, v, as_of)
    if row is None:
        raise ApiError(
            404,
            "replay_unavailable",
            f"The published model has no walk-forward estimate for {COUNTRY} at {as_of}.",
        )
    rows = _vintage_rows(session)
    archive_start = max(min(r.realtime_start for r in series) for series in rows.values())
    cutoff = period_end(as_of)
    base: dict[str, Any] = {
        "country": COUNTRY,
        "horizon": horizon,
        "as_of": as_of,
        "cutoff": cutoff,
        "vintage_date": cutoff,
        "archive_start": archive_start,
        "model_id": v.id,
        "fold_year": row.fold_year,
        "revised_probability": row.probability,
        "computed_at": datetime.now(UTC),
        "note": (
            "GDP, CPI inflation and unemployment as published on the cut-off date (ALFRED); market "
            "rates are not revised. The fold model was trained on today's revised history and the "
            "outcome is judged on today's GDP."
        ),
    }

    def unavailable(reason: str) -> dict[str, Any]:
        return base | {
            "available": False,
            "reason": reason,
            "reproduced": None,
            "vintage_probability": None,
            "vintage_band": None,
            "inputs": [],
        }

    if cutoff < archive_start:
        return unavailable(
            f"ALFRED holds all three US vintages only from {archive_start.isoformat()}; "
            f"{as_of} ended before that."
        )
    revised_inputs, _ = country_inputs(session, COUNTRY)
    revised = inference.snapshot_for(revised_inputs, as_of)
    first_known = inference.snapshot_for(vintage_inputs(revised_inputs, rows, cutoff), as_of)
    if revised is None or first_known is None:
        return unavailable(
            "The input set could not be rebuilt from the "
            + ("stored series" if revised is None else f"vintage of {cutoff.isoformat()}")
            + " with the usual publication lags."
        )
    if row.fold_year is None:
        return unavailable(
            "The stored estimate has no fold year, so its model cannot be re-fitted."
        )
    model = _fold_model(session, v, row.fold_year)
    if model is None:
        return unavailable(f"The {row.fold_year} fold could not be re-fitted from today's data.")
    reproduced = predict_one(model, revised.values)
    if abs(reproduced - row.probability) > REPRODUCE_TOLERANCE:
        return unavailable(
            "Re-fitting the fold model does not reproduce the stored estimate "
            f"({reproduced:.4f} vs {row.probability:.4f}): the stored data changed after training "
            f"run {v.run_id}. Retrain (`uv run macropulse train`) before comparing."
        )
    p = predict_one(model, first_known.values)
    return base | {
        "available": True,
        "reason": None,
        "reproduced": True,
        "vintage_probability": p,
        "vintage_band": inference.risk_band(p),
        "inputs": _compare(revised, first_known),
    }
