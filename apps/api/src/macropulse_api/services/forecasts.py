"""Indicator forecasts from stored official series (rolling-origin backtests, empirical intervals).

The forecast origin is the newest observation that had been published by the cut-off (the as-of
quarter end, or today), using the same conservative publication lags as the recession features.
Observations after the origin are returned as `realised` so a past as-of can be checked.
"""

from __future__ import annotations

import threading
from datetime import UTC, date, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from macropulse_api.db import as_utc
from macropulse_api.errors import ApiError
from macropulse_api.services.series_data import load_indicator, provenance, resolve_indicator
from macropulse_economics.periods import period_end, shift
from macropulse_ml.features import LAG_DAYS
from macropulse_ml.forecast import (
    FORECAST_VERSION,
    MIN_ERRORS,
    MODELS,
    MONTHLY,
    NOMINAL,
    QUARTERLY,
    Config,
    ForecastResult,
    run_forecast,
)
from macropulse_ml.target import quarter_index

# indicator -> (publication lag key, config, steps per quarter of horizon)
SUPPORTED: dict[str, tuple[str, Config, int]] = {
    "real_gdp_qoq": ("gdp", QUARTERLY, 1),
    "inflation_yoy": ("inflation", MONTHLY, 3),
    "unemployment_rate": ("unemployment", MONTHLY, 3),
}
HORIZONS_Q = (1, 2, 4, 8)
ASSUMPTIONS = [
    "Forecasts are statistical extrapolations of one series; they ignore policy changes and "
    "shocks.",
    "Intervals (nominal 80 %) are the 10th to 90th percentiles of each model's own past forecast "
    "errors at that step; they assume future errors resemble past ones. Their measured coverage "
    "in the backtest is shown — at long horizons it falls short of 80 %.",
    "Errors include crisis periods (2008-09, COVID-2020); RMSE is dominated by them.",
    "Inputs are latest revised data, not the figures available at the time.",
    "No seasonal-naive baseline: the series are seasonally adjusted or year-on-year rates.",
]

_lock = threading.Lock()
_cache: dict[tuple[str, str, str, int], ForecastResult] = {}


def _key(p: str) -> tuple[int, int]:
    return (quarter_index(p), 0) if "-Q" in p else (int(p[:4]), int(p[5:7]))


def _grid(points: dict[str, float], first: str, last: str) -> tuple[list[str], np.ndarray]:
    periods, p = [], first
    while True:
        periods.append(p)
        if p == last:
            break
        p = shift(p, 1)
    return periods, np.array([points.get(q, np.nan) for q in periods], dtype=np.float64)


def _cached(key: tuple[str, str, str, int], y: np.ndarray, cfg: Config) -> ForecastResult:
    with _lock:
        hit = _cache.get(key)
    if hit is not None:
        return hit
    result = run_forecast(y, cfg)
    with _lock:
        if len(_cache) > 128:
            _cache.clear()
        _cache[key] = result
    return result


def forecast(
    session: Session,
    iso2: str,
    metric: str,
    horizon_q: int,
    as_of: str | None,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    if metric not in SUPPORTED:
        raise ApiError(
            422,
            "unsupported_metric",
            f"No forecast for '{metric}'.",
            {"supported": list(SUPPORTED)},
        )
    if horizon_q not in HORIZONS_Q:
        raise ApiError(
            422,
            "unsupported_horizon",
            f"Horizon {horizon_q} is not supported.",
            {"supported": list(HORIZONS_Q)},
        )
    day = today or datetime.now(UTC).date()
    if as_of is not None and period_end(as_of) - timedelta(days=92) > day:
        raise ApiError(422, "invalid_as_of", f"As-of quarter {as_of} is in the future.")
    cutoff = min(period_end(as_of), day) if as_of else day

    lag_key, cfg, per_q = SUPPORTED[metric]
    data = load_indicator(session, iso2, resolve_indicator(metric))
    points = dict(data.points)
    # Latest: everything stored has been published (it was fetched). Past as-of: only what the
    # conservative publication lag says was out by the cut-off.
    lag = timedelta(days=LAG_DAYS[lag_key])
    eligible = sorted(
        (p for p in points if as_of is None or period_end(p) + lag <= cutoff), key=_key
    )
    if len(eligible) < cfg.min_train:
        raise ApiError(
            404,
            "forecast_unavailable",
            f"Fewer than {cfg.min_train} observations had been published by {cutoff}.",
        )
    origin = eligible[-1]
    first = min(points, key=_key)
    periods, y = _grid(points, first, origin)
    stamp = str(as_utc(data.latest_row.retrieved_at))
    result = _cached((data.series_id, stamp, origin, len(y)), y, cfg)

    steps = horizon_q * per_q
    later = sorted((p for p in points if _key(p) > _key(origin)), key=_key)
    models = []
    for key, mf in result.models.items():
        name, description = MODELS[key]
        models.append(
            {
                "key": key,
                "name": name,
                "description": description,
                "available": mf.available,
                "reason": mf.reason,
                "path": [
                    {
                        "period": shift(origin, pt.step),
                        "step": pt.step,
                        "value": pt.value,
                        "lower": pt.lower,
                        "upper": pt.upper,
                        "n_errors": pt.n_errors,
                    }
                    for pt in mf.path
                    if pt.step <= steps
                ],
            }
        )
    metrics = []
    for key, mf in result.models.items():
        for s, m in sorted(mf.metrics.items()):
            metrics.append(
                {
                    "model": key,
                    "step": s,
                    "horizon_quarters": s // per_q,
                    "n": m.n,
                    "mae": m.mae,
                    "rmse": m.rmse,
                    "bias": m.bias,
                    "rel_rmse": m.rel_rmse,
                    "coverage": m.coverage,
                    "coverage_n": m.coverage_n,
                    "mean_width": m.mean_width,
                    "note": m.note,
                }
            )
    errors = [
        {
            "model": key,
            "origin": periods[e.origin],
            "target": periods[e.target],
            "forecast": e.forecast,
            "actual": e.actual,
            "error": e.error,
        }
        for key, mf in result.models.items()
        for e in mf.errors.get(steps, [])
    ]
    return {
        "country": iso2,
        "metric": metric,
        "indicator_name": data.indicator.name,
        "unit": data.unit,
        "frequency": data.indicator.frequency.value,
        "horizon_quarters": horizon_q,
        "steps": steps,
        "as_of": as_of,
        "cutoff": cutoff,
        "origin": origin,
        "version": FORECAST_VERSION,
        "nominal_coverage": NOMINAL,
        "min_errors": MIN_ERRORS,
        "actuals": [
            {"period": p, "value": float(v)}
            for p, v in zip(periods, y, strict=True)
            if not np.isnan(v)
        ],
        "realised": [{"period": p, "value": points[p]} for p in later[:steps]],
        "models": models,
        "backtest": {
            "first_origin": periods[result.first_origin]
            if result.first_origin is not None
            else None,
            "last_origin": periods[result.last_origin] if result.last_origin is not None else None,
            "metrics": metrics,
        },
        "errors": errors,
        "assumptions": ASSUMPTIONS,
        "transform": data.transform.description,
        "provenance": provenance(session, data),
        "generated_at": datetime.now(UTC),
    }
