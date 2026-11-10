"""Forecast engine: timing (no look-ahead), honest interval coverage, baselines and missing data.

Synthetic series test mechanics only; they never stand for forecast quality on official data.
"""

from __future__ import annotations

import numpy as np
import pytest

from macropulse_ml.forecast import MIN_ERRORS, QUARTERLY, Config, run_forecast

SMALL = Config(lags=2, mean_window=8, eval_steps=(1, 2), max_step=2, min_train=30)


def _ar1(n: int, phi: float = 0.8, sd: float = 1.0, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + sd * rng.standard_normal()
    return y


def test_baselines_are_the_last_value_and_the_recent_mean() -> None:
    y = _ar1(120)
    result = run_forecast(y, QUARTERLY)
    assert result.origin == 119
    naive = result.models["naive"].path
    mean = result.models["mean"].path
    assert [p.step for p in naive] == list(range(1, QUARTERLY.max_step + 1))
    assert all(p.value == pytest.approx(y[-1]) for p in naive)
    assert all(p.value == pytest.approx(y[-QUARTERLY.mean_window :].mean()) for p in mean)


def test_forecasts_never_use_values_after_their_origin() -> None:
    """Every forecast scored in a backtest on a truncated series is identical in the full run:
    a forecast issued at origin o depends on y[0..o] only."""
    y = _ar1(220)
    k = 160
    full = run_forecast(y, QUARTERLY)
    short = run_forecast(y[:k], QUARTERLY)
    for model in ("naive", "mean", "ar"):
        for step in QUARTERLY.eval_steps:
            a = [(e.origin, e.forecast) for e in short.models[model].errors[step]]
            b = [(e.origin, e.forecast) for e in full.models[model].errors[step] if e.target < k]
            assert a, (model, step)
            assert [o for o, _ in a] == [o for o, _ in b]
            assert np.allclose([f for _, f in a], [f for _, f in b])


def test_errors_are_scored_only_against_realised_targets() -> None:
    y = _ar1(150)
    result = run_forecast(y, QUARTERLY)
    for model in result.models.values():
        for step, errs in model.errors.items():
            assert all(e.target == e.origin + step <= result.origin for e in errs)
            assert all(e.actual == pytest.approx(y[e.target]) for e in errs)


def test_ar_beats_naive_on_a_mean_reverting_series() -> None:
    result = run_forecast(_ar1(400, phi=0.5), QUARTERLY)
    for step in (1, 4):
        ar = result.models["ar"].metrics[step]
        assert ar.rel_rmse is not None
        assert ar.rel_rmse < 0.95
    assert result.models["naive"].metrics[1].rel_rmse == pytest.approx(1.0)


def test_coverage_is_out_of_sample_and_exposes_a_volatility_break() -> None:
    """Intervals come from errors already known at each origin. After a jump in volatility the
    old, narrow intervals miss far more than 20 % of the time; an in-sample interval would hide
    that."""
    calm = _ar1(200, phi=0.5, sd=0.1, seed=5)
    wild = _ar1(200, phi=0.5, sd=2.0, seed=6)
    result = run_forecast(np.concatenate([calm, wild]), QUARTERLY)
    m = result.models["ar"].metrics[1]
    assert m.coverage is not None
    assert m.coverage < 0.7
    stable = run_forecast(_ar1(400, phi=0.5, seed=7), QUARTERLY).models["ar"].metrics[1]
    assert stable.coverage is not None
    assert 0.7 < stable.coverage < 0.9


def test_intervals_need_enough_past_errors() -> None:
    y = _ar1(SMALL.min_train + MIN_ERRORS - 5)
    result = run_forecast(y, SMALL)
    path = result.models["naive"].path
    assert all(p.lower is None and p.upper is None for p in path)
    assert all(p.n_errors < MIN_ERRORS for p in path)
    assert result.models["naive"].metrics[1].rmse is None
    assert "needs" in (result.models["naive"].metrics[1].note or "")

    longer = run_forecast(_ar1(200), SMALL).models["naive"].path
    for p in longer:
        assert p.lower is not None
        assert p.upper is not None
        assert p.lower < p.value < p.upper


def test_missing_values_are_never_filled() -> None:
    y = _ar1(150)
    y[-2] = np.nan  # a missing official value right before the origin
    y[60] = np.nan
    result = run_forecast(y, QUARTERLY)
    ar = result.models["ar"]
    assert ar.available is False
    assert ar.path == []
    assert "consecutive" in (ar.reason or "")
    assert result.models["naive"].available is True
    for model in result.models.values():
        for errs in model.errors.values():
            assert all(not np.isnan(e.actual) and e.target not in (60, 148) for e in errs)
