"""Re-fitting one walk-forward fold reproduces the backtest's stored estimates exactly."""

from __future__ import annotations

import pytest
from ml_synthetic import synthetic_inputs

from macropulse_ml.backtest import HorizonResult, run_horizon
from macropulse_ml.panel import Panel, build_panel
from macropulse_ml.refit import fold_model, predict_one

SEED = 7


@pytest.fixture(scope="module")
def panel() -> Panel:
    inputs = [synthetic_inputs("AA", 1), synthetic_inputs("BB", 2, event_dated_rate=True)]
    return build_panel(inputs, "1977-Q1", "2026-Q3", (4,))


@pytest.fixture(scope="module")
def backtest(panel: Panel) -> HorizonResult:
    return run_horizon(panel, 4, seed=SEED, last_year=2026)


@pytest.mark.parametrize(
    "key", ["logistic", "hist_gbm", "hist_gbm_platt", "mlp", "contraction_rule"]
)
def test_refitted_fold_model_reproduces_the_walk_forward_estimates(
    panel: Panel, backtest: HorizonResult, key: str
) -> None:
    rows = {(r.country, r.as_of): r for r in panel.rows}
    for year in (2003, 2015):
        model = fold_model(panel, 4, key, seed=SEED, fold_year=year)
        assert model is not None
        stored = [p for p in backtest.results[key].predictions if p.fold_year == year]
        assert stored
        for p in stored:
            row = rows[(p.country, p.as_of)]
            values = dict(zip(panel.feature_names, row.x, strict=True))
            assert predict_one(model, values) == pytest.approx(p.probability, abs=1e-12)


def test_skipped_or_unknown_folds(panel: Panel) -> None:
    assert fold_model(panel, 4, "logistic", seed=SEED, fold_year=2040) is None  # no test rows
    with pytest.raises(KeyError):
        fold_model(panel, 4, "no_such_model", seed=SEED, fold_year=2010)
