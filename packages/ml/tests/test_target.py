from __future__ import annotations

import pytest

from macropulse_ml.target import LabelStatus, technical_recession_label, technical_recessions


def _g(start: str, values: list[float]) -> dict[str, float]:
    year, q = (int(x) for x in start.split("-Q"))
    out: dict[str, float] = {}
    for v in values:
        out[f"{year}-Q{q}"] = v
        q += 1
        if q == 5:
            year, q = year + 1, 1
    return out


# as_of 2020-Q1, so the window starts at 2020-Q2
@pytest.mark.parametrize(
    ("values", "h2", "h4"),
    [
        ([-0.1, -0.2, 0.3, 0.3], 1, 1),  # pair in t+1, t+2
        ([-0.1, 0.0, -0.2, 0.5], 0, 0),  # zero breaks the pair: zero is not negative
        ([0.3, -0.1, -0.1, 0.2], 0, 1),  # pair in t+2, t+3: only inside the 4-quarter window
        ([0.3, 0.2, 0.1, -0.5], 0, 0),  # a single negative quarter is not an event
        ([0.3, 0.2, -0.1, -0.5], 0, 1),  # pair at the very end of the H=4 window
    ],
)
def test_methodology_cases(values: list[float], h2: int, h4: int) -> None:
    g = _g("2020-Q2", values) | {"2020-Q1": 0.4}
    assert technical_recession_label(g, "2020-Q1", 2, "2020-Q4").value == h2
    assert technical_recession_label(g, "2020-Q1", 4, "2021-Q1").value == h4


def test_window_is_strictly_after_the_as_of_quarter() -> None:
    # negative quarters at t and t+1 do not make a pair inside t+1 … t+2
    g = {"2020-Q1": -1.0, "2020-Q2": -1.0, "2020-Q3": 0.5}
    lab = technical_recession_label(g, "2020-Q1", 2, "2020-Q3")
    assert lab.window == ("2020-Q2", "2020-Q3")
    assert lab.value == 0


def test_incomplete_future_is_censored_not_negative() -> None:
    g = _g("2026-Q1", [0.2, 0.1, -0.3])
    lab = technical_recession_label(g, "2026-Q1", 4, "2026-Q3")
    assert lab.status is LabelStatus.CENSORED
    assert lab.value is None


def test_missing_quarter_is_excluded_not_negative() -> None:
    g = _g("2019-Q1", [0.2, 0.1, 0.3, 0.2, 0.1])
    del g["2019-Q3"]
    lab = technical_recession_label(g, "2019-Q1", 4, "2020-Q1")
    assert lab.status is LabelStatus.MISSING
    assert lab.value is None


def test_horizon_must_hold_a_pair() -> None:
    with pytest.raises(ValueError):
        technical_recession_label({}, "2020-Q1", 1, "2020-Q2")


def test_event_dating_finds_runs_and_respects_gaps() -> None:
    g = _g("2008-Q1", [0.3, -0.5, -1.8, -2.1, -0.4, 0.2, -0.1, 0.1, -0.2, -0.3])
    assert technical_recessions(g) == [("2008-Q2", "2009-Q1"), ("2010-Q1", "2010-Q2")]
    gap = {"2008-Q2": -0.5, "2008-Q4": -0.3}  # not consecutive
    assert technical_recessions(gap) == []
