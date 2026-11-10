"""Indicator forecasts with rolling-origin backtests and empirical intervals.

Models (fixed in advance, deterministic):
- `naive`: the last observed value (random walk) — the reference every model must beat.
- `mean`: mean of the last W observations (W = 20 quarters / 60 months) — a mean-reversion baseline.
- `ar`: direct multi-step autoregression — for each step s, ridge regression of y[t+s] on
  y[t] … y[t-p+1] (p = 4 quarterly, 6 monthly), refitted at every origin on data known then.
A seasonal-naive baseline is not used: the series are seasonally adjusted or year-on-year rates.

Backtest: every origin from the first with enough history; a forecast for step s made at origin o
is scored against the actual at o+s. Interval (nominal 80 %): forecast plus the 10th/90th
percentile of the model's past errors at that step — only errors whose target was already
observed at the origin, so coverage is measured honestly out of sample.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

FORECAST_VERSION = "forecast-v1"
NOMINAL = 0.8
Q_LO, Q_HI = 0.1, 0.9
MIN_ERRORS = 20  # past errors needed before an interval is issued
RIDGE_ALPHA = 1.0
MODELS: dict[str, tuple[str, str]] = {
    "naive": ("Naive (last value)", "Random walk: every future value equals the last observation."),
    "mean": ("Rolling mean", "Mean of the most recent observations (20 quarters / 60 months)."),
    "ar": (
        "Direct ridge AR",
        "One ridge regression per step on the latest p values (p = 4 quarters / 6 months), "
        "refitted at every origin on data known at that time.",
    ),
}


@dataclass(frozen=True)
class Config:
    lags: int
    mean_window: int
    eval_steps: tuple[int, ...]
    max_step: int
    min_train: int = 40
    max_origins: int = 400  # most recent origins backtested (bounded cost, recent relevance)


QUARTERLY = Config(lags=4, mean_window=20, eval_steps=(1, 2, 4, 8), max_step=8)
MONTHLY = Config(lags=6, mean_window=60, eval_steps=(3, 6, 12, 24), max_step=24)


@dataclass
class ErrorRecord:
    origin: int
    target: int
    forecast: float
    actual: float

    @property
    def error(self) -> float:
        return self.actual - self.forecast


@dataclass
class StepMetrics:
    n: int
    mae: float | None
    rmse: float | None
    bias: float | None
    rel_rmse: float | None  # RMSE / naive RMSE on the same origins
    coverage: float | None  # share of actuals inside the 80 % interval (past-errors only)
    coverage_n: int
    mean_width: float | None
    note: str | None = None


@dataclass
class PathPoint:
    step: int
    value: float
    lower: float | None
    upper: float | None
    n_errors: int


@dataclass
class ModelForecast:
    key: str
    available: bool
    reason: str | None = None
    path: list[PathPoint] = field(default_factory=list)
    metrics: dict[int, StepMetrics] = field(default_factory=dict)
    errors: dict[int, list[ErrorRecord]] = field(default_factory=dict)


@dataclass
class ForecastResult:
    origin: int  # index of the last observation used
    first_origin: int | None
    last_origin: int | None
    models: dict[str, ModelForecast]


class _Ridge:
    """Expanding-window ridge for one step, updated one row at a time (normal equations)."""

    def __init__(self, k: int) -> None:
        self.xtx = np.zeros((k, k))
        self.xty = np.zeros(k)
        self.n = 0
        self.penalty = np.eye(k) * RIDGE_ALPHA
        self.penalty[0, 0] = 0.0  # never shrink the intercept

    def add(self, x: NDArray[np.float64], y: float) -> None:
        self.xtx += np.outer(x, x)
        self.xty += x * y
        self.n += 1

    def predict(self, x: NDArray[np.float64]) -> float | None:
        if self.n < x.size + 5:
            return None
        coef = np.linalg.solve(self.xtx + self.penalty, self.xty)
        return float(x @ coef)


def _lag_vector(y: NDArray[np.float64], t: int, lags: int) -> NDArray[np.float64] | None:
    if t - lags + 1 < 0:
        return None
    window = y[t - lags + 1 : t + 1][::-1]
    if np.isnan(window).any():
        return None
    return np.concatenate(([1.0], window))


def _mean(y: NDArray[np.float64], t: int, w: int) -> float | None:
    window = y[max(0, t - w + 1) : t + 1]
    window = window[~np.isnan(window)]
    return float(window.mean()) if window.size >= min(w, 8) else None


def run_forecast(  # noqa: PLR0912, PLR0915 - one tight loop; splitting would hide the timing rules
    y: NDArray[np.float64], cfg: Config
) -> ForecastResult:
    """`y` is the series on a contiguous period grid ending at the forecast origin; missing
    official values are NaN and are never filled."""
    n = len(y)
    origin = n - 1
    first = min(max(cfg.min_train, cfg.lags, n - cfg.max_origins), origin)
    ridges = {s: _Ridge(cfg.lags + 1) for s in range(1, cfg.max_step + 1)}
    errors: dict[str, dict[int, list[ErrorRecord]]] = {
        m: {s: [] for s in range(1, cfg.max_step + 1)} for m in MODELS
    }
    # issued[m][s] = list of (origin, forecast, lower, upper) for coverage, using past errors only
    issued: dict[str, dict[int, list[tuple[int, float, float, float]]]] = {
        m: {s: [] for s in range(1, cfg.max_step + 1)} for m in MODELS
    }
    err_origins: dict[str, dict[int, list[int]]] = {
        m: {s: [] for s in range(1, cfg.max_step + 1)} for m in MODELS
    }
    err_values: dict[str, dict[int, list[float]]] = {
        m: {s: [] for s in range(1, cfg.max_step + 1)} for m in MODELS
    }
    eval_steps = set(cfg.eval_steps)

    def add_rows_until(o: int) -> None:
        # rows (t -> t+s) are known at origin o when t + s <= o
        for s, ridge in ridges.items():
            t = o - s
            if t >= 0 and not np.isnan(y[o]):
                x = _lag_vector(y, t, cfg.lags)
                if x is not None:
                    ridge.add(x, float(y[o]))

    for o in range(0, first):
        add_rows_until(o)

    def forecasts_at(o: int) -> dict[str, dict[int, float | None]]:
        last = y[o]
        x = _lag_vector(y, o, cfg.lags)
        mean = _mean(y, o, cfg.mean_window)
        out: dict[str, dict[int, float | None]] = {m: {} for m in MODELS}
        for s in range(1, cfg.max_step + 1):
            out["naive"][s] = None if np.isnan(last) else float(last)
            out["mean"][s] = mean
            out["ar"][s] = ridges[s].predict(x) if x is not None else None
        return out

    last_origin: int | None = None
    for o in range(first, origin + 1):
        add_rows_until(o)
        if o == origin:
            break
        fc = forecasts_at(o)
        for m, by_step in fc.items():
            for s, f in by_step.items():
                if f is None:
                    continue
                if s in eval_steps:
                    # errors are appended in origin order; those known at o have origin <= o - s
                    k = bisect_right(err_origins[m][s], o - s)
                    if k >= MIN_ERRORS:
                        lo, hi = np.quantile(err_values[m][s][:k], [Q_LO, Q_HI])
                        issued[m][s].append((o, f, f + float(lo), f + float(hi)))
                if o + s <= origin and not np.isnan(y[o + s]):
                    rec = ErrorRecord(o, o + s, f, float(y[o + s]))
                    errors[m][s].append(rec)
                    err_origins[m][s].append(o)
                    err_values[m][s].append(rec.error)
        last_origin = o

    final = forecasts_at(origin)
    models: dict[str, ModelForecast] = {}
    for m in MODELS:
        mf = ModelForecast(key=m, available=True, errors=errors[m])
        for s in range(1, cfg.max_step + 1):
            f = final[m][s]
            if f is None:
                continue
            past = [e.error for e in errors[m][s]]
            if len(past) >= MIN_ERRORS:
                lo, hi = np.quantile(past, [Q_LO, Q_HI])
                mf.path.append(PathPoint(s, f, f + float(lo), f + float(hi), len(past)))
            else:
                mf.path.append(PathPoint(s, f, None, None, len(past)))
        if not mf.path:
            mf.available = False
            mf.reason = (
                "Not enough complete recent history at the forecast origin "
                f"(needs {cfg.lags} consecutive published values)."
                if m == "ar"
                else "No usable history at the forecast origin."
            )
        models[m] = mf
    _score(models, errors, issued, cfg, y)
    return ForecastResult(origin, first if last_origin is not None else None, last_origin, models)


def _score(
    models: dict[str, ModelForecast],
    errors: dict[str, dict[int, list[ErrorRecord]]],
    issued: dict[str, dict[int, list[tuple[int, float, float, float]]]],
    cfg: Config,
    y: NDArray[np.float64],
) -> None:
    for s in cfg.eval_steps:
        naive = {e.origin: e.error for e in errors["naive"][s]}
        for m, mf in models.items():
            errs = errors[m][s]
            if len(errs) < MIN_ERRORS:
                mf.metrics[s] = StepMetrics(
                    len(errs),
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    None,
                    note=f"Only {len(errs)} scored forecasts (needs {MIN_ERRORS}).",
                )
                continue
            e = np.array([r.error for r in errs])
            common = [(r.error, naive[r.origin]) for r in errs if r.origin in naive]
            rel = None
            if common:
                me, ne = np.array(common).T
                naive_rmse = float(np.sqrt(np.mean(ne**2)))
                rel = float(np.sqrt(np.mean(me**2)) / naive_rmse) if naive_rmse > 0 else None
            hits, widths = [], []
            for o, _f, lo, hi in issued[m][s]:
                if o + s < len(y) and not np.isnan(y[o + s]):
                    hits.append(lo <= y[o + s] <= hi)
                    widths.append(hi - lo)
            mf.metrics[s] = StepMetrics(
                n=len(errs),
                mae=float(np.mean(np.abs(e))),
                rmse=float(np.sqrt(np.mean(e**2))),
                bias=float(np.mean(e)),
                rel_rmse=rel,
                coverage=float(np.mean(hits)) if hits else None,
                coverage_n=len(hits),
                mean_width=float(np.mean(widths)) if widths else None,
                note=None if hits else "No interval could be issued from past errors yet.",
            )
