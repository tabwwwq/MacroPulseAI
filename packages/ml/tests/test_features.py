"""As-of eligibility and leakage tests for feature snapshots."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from ml_synthetic import synthetic_inputs

from macropulse_economics.periods import period_end
from macropulse_ml.features import (
    FEATURE_NAMES,
    LAG_DAYS,
    CountryInputs,
    _expected_latest_month,
    snapshots,
)


@pytest.mark.parametrize(
    ("cutoff", "lag", "expected"),
    [
        (date(2026, 3, 31), 30, "2026-02"),
        (date(2026, 3, 31), 45, "2026-01"),
        (date(2026, 6, 30), 30, "2026-05"),
        (date(2026, 3, 31), 7, "2026-02"),
        (date(2026, 3, 31), 0, "2026-03"),
    ],
)
def test_expected_latest_month(cutoff: date, lag: int, expected: str) -> None:
    assert _expected_latest_month(cutoff, lag) == expected


def _one(inputs: CountryInputs, as_of: str):  # type: ignore[no-untyped-def]
    snaps = snapshots(inputs, as_of, as_of)
    assert len(snaps) == 1, "snapshot not computable"
    return snaps[0]


def test_snapshot_uses_only_published_periods() -> None:
    s = _one(synthetic_inputs("AA", 1), "2010-Q1")
    assert s.used["gdp_qoq_1"] == "2009-Q4"
    assert s.used["gdp_qoq_2"] == "2009-Q3"
    assert s.used["infl_yoy"] == "2010-02"
    assert s.used["unemp"] == "2010-01"
    assert s.used["rate"] == "2010-02"  # monthly average, 7-day lag
    assert set(s.values) == set(FEATURE_NAMES)


def test_leakage_future_values_cannot_change_a_snapshot() -> None:
    base = synthetic_inputs("AA", 1)
    as_of = "2010-Q1"
    cutoff = period_end(as_of)

    def poison(series: dict[str, float], lag: int) -> dict[str, float]:
        return {
            p: (
                v if (period_end(p) - cutoff).days + lag <= 0 and period_end(p) <= cutoff else 999.0
            )
            for p, v in series.items()
        }

    poisoned = replace(
        base,
        gdp_qoq={
            p: (v if period_end(p) <= date(2009, 12, 31) else 999.0)
            for p, v in base.gdp_qoq.items()
        },
        gdp_yoy={
            p: (v if period_end(p) <= date(2009, 12, 31) else 999.0)
            for p, v in base.gdp_yoy.items()
        },
        inflation={
            p: (v if period_end(p) <= date(2010, 2, 28) else 999.0)
            for p, v in base.inflation.items()
        },
        unemployment={
            p: (v if period_end(p) <= date(2010, 1, 31) else 999.0)
            for p, v in base.unemployment.items()
        },
        policy_rate={
            p: (v if period_end(p) <= date(2010, 2, 28) else 999.0)
            for p, v in base.policy_rate.items()
        },
    )
    assert _one(base, as_of).values == _one(poisoned, as_of).values
    assert poison  # helper kept for readability of intent


def test_quarter_being_reported_is_not_visible() -> None:
    base = synthetic_inputs("AA", 1)
    changed = replace(base, gdp_qoq=base.gdp_qoq | {"2010-Q1": -50.0})
    assert _one(base, "2010-Q1").values == _one(changed, "2010-Q1").values


def test_missing_gdp_for_previous_quarter_excludes_the_snapshot() -> None:
    base = synthetic_inputs("AA", 1)
    gdp = dict(base.gdp_qoq)
    del gdp["2009-Q4"]
    assert snapshots(replace(base, gdp_qoq=gdp), "2010-Q1", "2010-Q1") == []


def test_one_missing_month_falls_back_and_is_flagged_two_exclude() -> None:
    base = synthetic_inputs("AA", 1)
    one_gap = {k: v for k, v in base.unemployment.items() if k != "2010-01"}
    s = _one(replace(base, unemployment=one_gap), "2010-Q1")
    assert s.used["unemp"] == "2009-12"
    assert s.stale == ("unemployment",)
    two_gaps = {k: v for k, v in one_gap.items() if k != "2009-12"}
    assert snapshots(replace(base, unemployment=two_gaps), "2010-Q1", "2010-Q1") == []


def test_event_dated_rate_uses_the_decision_in_force() -> None:
    base = synthetic_inputs("BB", 2, event_dated_rate=True)
    rate = {"2008-11-15": 3.0, "2009-03-15": 1.5, "2010-03-15": 1.0, "2010-04-15": 0.5}
    s = _one(replace(base, policy_rate=rate), "2010-Q1")
    assert s.values["rate"] == 1.0  # decided 2010-03-15, before 2010-03-31
    assert s.values["rate_chg_4q"] == pytest.approx(-0.5)  # vs 1.5 in force on 2009-03-31
    assert LAG_DAYS["policy_rate_event"] == 0
