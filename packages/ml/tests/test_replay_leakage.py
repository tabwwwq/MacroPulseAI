"""Temporal leakage tests for historical replay.

A replay at as-of D shows the walk-forward estimate for D. These tests prove that estimate depends
on nothing that was unpublished at D: deleting every observation published after D (features *and*
the outcomes later models learn from) must reproduce exactly the same probabilities.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from macropulse_economics.periods import period_end, shift
from macropulse_ml.backtest import run_horizon
from macropulse_ml.features import LAG_DAYS, CountryInputs
from macropulse_ml.panel import build_panel
from macropulse_ml.splits import walk_forward
from macropulse_ml.target import quarter_index

REPLAY = "2008-Q2"


def published_by(inputs: CountryInputs, as_of: str) -> CountryInputs:
    """Only what had been published by the end of `as_of`, under the model's lag assumptions."""
    cutoff = period_end(as_of)

    def keep(series: dict[str, float], lag: int) -> dict[str, float]:
        return {p: v for p, v in series.items() if period_end(p) + timedelta(days=lag) <= cutoff}

    rate_lag = LAG_DAYS[
        "policy_rate_event" if inputs.policy_rate_event_dated else "policy_rate_monthly"
    ]
    return replace(
        inputs,
        gdp_qoq=keep(inputs.gdp_qoq, LAG_DAYS["gdp"]),
        gdp_yoy=keep(inputs.gdp_yoy, LAG_DAYS["gdp"]),
        inflation=keep(inputs.inflation, LAG_DAYS["inflation"]),
        unemployment=keep(inputs.unemployment, LAG_DAYS["unemployment"]),
        policy_rate=keep(inputs.policy_rate, rate_lag),
        bond_yield=keep(inputs.bond_yield, LAG_DAYS["rates_monthly"]),
        short_rate=keep(inputs.short_rate, LAG_DAYS["rates_monthly"]),
    )


@pytest.mark.parametrize("horizon", [2, 4])
def test_replay_estimate_is_identical_with_the_future_deleted(
    two_countries: list[CountryInputs], horizon: int
) -> None:
    year = int(REPLAY[:4])
    full = run_horizon(build_panel(two_countries, "1977-Q1", "2026-Q3"), horizon, 7, year)
    truncated_inputs = [published_by(c, REPLAY) for c in two_countries]
    past = run_horizon(build_panel(truncated_inputs, "1977-Q1", REPLAY), horizon, 7, year)

    compared = 0
    for key, res in full.results.items():
        if not res.available:
            continue
        a = {(p.country, p.as_of): p for p in res.predictions if p.as_of == REPLAY}
        b = {(p.country, p.as_of): p for p in past.results[key].predictions if p.as_of == REPLAY}
        assert a, key
        assert a.keys() == b.keys()
        for k, pa in a.items():
            assert pa.fold_year == b[k].fold_year == year
            assert pa.probability == pytest.approx(b[k].probability, abs=1e-12), (key, k)
            compared += 1
    assert compared >= 8  # several models x both countries


@pytest.mark.parametrize("horizon", [2, 4])
def test_every_training_outcome_was_published_before_its_test_quarters(
    two_countries: list[CountryInputs], horizon: int
) -> None:
    panel = build_panel(two_countries, "1977-Q1", "2026-Q3")
    folds, _ = walk_forward(panel, horizon, 2000, 2026)
    assert folds
    for fold in folds:
        first_test = min(panel.rows[i].as_of for i in fold.test)
        first_cutoff = period_end(first_test)
        for i in fold.train:
            last_label_quarter = shift(panel.rows[i].as_of, horizon)
            published = period_end(last_label_quarter) + timedelta(days=LAG_DAYS["gdp"])
            assert published <= first_cutoff, (fold.year, panel.rows[i].as_of)
        # and no test quarter lies before the earliest one checked above
        assert all(
            quarter_index(panel.rows[i].as_of) >= quarter_index(first_test) for i in fold.test
        )
