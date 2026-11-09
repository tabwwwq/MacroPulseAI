"""Walk-forward purge, train-only preprocessing, metric definitions and selection protocol."""

from __future__ import annotations

import numpy as np
import pytest

from macropulse_ml.backtest import DEV_END_YEAR, ModelResult, run_horizon, select
from macropulse_ml.features import CountryInputs
from macropulse_ml.metrics import MetricSet, evaluate
from macropulse_ml.models import SPECS, logistic
from macropulse_ml.panel import build_panel
from macropulse_ml.splits import walk_forward


@pytest.fixture
def panel(two_countries: list[CountryInputs]):  # type: ignore[no-untyped-def]
    return build_panel(two_countries, "1977-Q1", "2026-Q3")


@pytest.mark.parametrize("horizon", [2, 4])
def test_folds_are_purged_by_the_horizon_and_pooled_on_time(panel, horizon: int) -> None:  # type: ignore[no-untyped-def]
    folds, _ = walk_forward(panel, horizon, 2000, 2026)
    assert folds
    for f in folds:
        assert f.train_max_q + horizon <= f.test_min_q - 1  # labels fully observed before testing
        assert not set(f.train) & set(f.test)
        assert all(panel.rows[i].labels[horizon] is not None for i in f.train)
        # every country's quarters of the test year sit in the same fold
        assert {panel.rows[i].country for i in f.test} == {"AA", "BB"}


def test_scaler_is_fitted_on_training_rows_only(panel) -> None:  # type: ignore[no-untyped-def]
    fold = walk_forward(panel, 4, 2005, 2005)[0][0]
    x_train, y_train = panel.matrix(fold.train), panel.target(fold.train, 4)
    model = logistic(42).fit(x_train, y_train)
    scaler = model.named_steps["scale"]
    np.testing.assert_allclose(scaler.mean_, x_train.mean(axis=0))
    everything = panel.matrix(list(range(len(panel.rows))))
    assert not np.allclose(scaler.mean_, everything.mean(axis=0))


def test_censored_rows_never_enter_training_or_metrics(panel) -> None:  # type: ignore[no-untyped-def]
    result = run_horizon(panel, 4, seed=42, last_year=2026)
    latest = [r for r in panel.rows if r.as_of >= "2025-Q4"]
    assert latest and all(r.labels[4] is None for r in latest)
    preds = result.results["logistic"].predictions
    assert {p.split for p in preds if p.as_of >= "2025-Q4"} == {"unlabelled"}
    dev = result.results["logistic"].metrics["development"]
    assert dev.n == sum(1 for p in preds if p.split == "development")


def test_selection_uses_development_brier_only(panel) -> None:  # type: ignore[no-untyped-def]
    result = run_horizon(panel, 2, seed=42, last_year=2026)

    def dev(key: str) -> float:
        return result.results[key].metrics["development"].values["brier"] or 1e9

    candidates = [
        k for k, r in result.results.items() if r.spec.role == "candidate" and r.available
    ]
    best = min(candidates, key=dev)
    expected = (
        best if dev(best) < dev("prevalence") else min(("prevalence", "contraction_rule"), key=dev)
    )
    assert result.selected == expected
    assert result.selection_note
    assert all(
        p.fold_year is not None and p.fold_year <= DEV_END_YEAR
        for p in result.results[best].predictions
        if p.split == "development"
    )
    assert result.final_model is not None
    assert {p.country for p in result.live} == {"AA", "BB"}
    assert result.results["xgboost"].available or "not installed" in (
        result.results["xgboost"].unavailable_reason or ""
    )


def _result(key: str, role: str, dev_brier: float) -> ModelResult:
    spec = next(s for s in SPECS if s.key == key)
    assert spec.role == role
    r = ModelResult(spec, True)
    r.metrics["development"] = MetricSet(n=10, events=2, values={"brier": dev_brier})
    r.metrics["heldout"] = MetricSet(n=10, events=2, values={"brier": 0.0})  # must be ignored
    return r


def test_a_candidate_is_published_only_if_it_beats_the_baseline() -> None:
    wins = {
        "prevalence": _result("prevalence", "baseline", 0.20),
        "contraction_rule": _result("contraction_rule", "baseline", 0.19),
        "logistic": _result("logistic", "candidate", 0.15),
    }
    assert select(wins)[0] == "logistic"
    loses = wins | {"logistic": _result("logistic", "candidate", 0.25)}
    key, note = select(loses)
    assert key == "contraction_rule"
    assert "No candidate beats the prevalence baseline" in note


def test_reproducible_with_a_fixed_seed(panel) -> None:  # type: ignore[no-untyped-def]
    a = run_horizon(panel, 4, seed=7, last_year=2010)
    b = run_horizon(panel, 4, seed=7, last_year=2010)
    pa = [p.probability for p in a.results["hist_gbm"].predictions]
    pb = [p.probability for p in b.results["hist_gbm"].predictions]
    assert pa == pb


def test_undefined_metrics_are_none_with_a_reason() -> None:
    m = evaluate(np.array([0, 0, 0]), np.array([0.1, 0.2, 0.3]))
    assert m.values["roc_auc"] is None and "one class" in m.notes["roc_auc"]
    assert m.values["precision"] is None
    assert m.values["recall"] is None
    assert m.values["brier"] == pytest.approx((0.01 + 0.04 + 0.09) / 3)


def test_metric_values_and_calibration_bins() -> None:
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.6, 0.4, 0.9])
    m = evaluate(y, p, reference=np.full(4, 0.5))
    assert m.values["roc_auc"] == pytest.approx(0.75)
    assert m.confusion == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert m.values["brier_skill"] == pytest.approx(1 - m.values["brier"] / 0.25)  # type: ignore[operator]
    assert sum(b["count"] for b in m.calibration) == 4
