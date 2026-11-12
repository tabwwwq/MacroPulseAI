from __future__ import annotations

from datetime import UTC, date, datetime

from macropulse_economics.connectors import FetchedObservation, FetchResult, SeriesRequest
from macropulse_economics.quality import run_checks
from macropulse_economics.series import native_series

TODAY = date(2026, 11, 9)
Q_REQ = SeriesRequest("eurostat", "namq_10_gdp", "k", "DE", "quarterly", "Chain-linked volumes")
M_REQ = SeriesRequest("eurostat", "une_rt_m", "k", "DE", "monthly", "% of labour force")


def _result(req: SeriesRequest, points: list[tuple[str, float, str | None]]) -> FetchResult:
    return FetchResult(
        request=req,
        observations=[FetchedObservation(p, v, s) for p, v, s in points],
        url="https://example.test",
        retrieved_at=datetime(2026, 11, 9, tzinfo=UTC),
    )


def _by_rule(result: FetchResult) -> dict[str, tuple[str, str]]:
    return {c.rule: (c.status, c.detail) for c in run_checks(result, TODAY)}


# --- native series ----------------------------------------------------------------------------


def test_gdp_levels_are_fetched_once_for_both_growth_indicators() -> None:
    reqs, _ = native_series(["DE"], ["eurostat"])
    gdp = [r for r in reqs if r.dataset == "namq_10_gdp"]
    assert len(gdp) == 1
    assert gdp[0].indicator_ids == ("real_gdp_qoq", "real_gdp_yoy")


def test_ecb_rate_is_one_shared_euro_area_series() -> None:
    reqs, _ = native_series(["BE", "DE", "FR", "NL"], ["ecb"])
    assert len(reqs) == 1
    assert reqs[0].geo == "EA"
    assert reqs[0].series_key == "B.U2.EUR.4F.KR.DFR.LEV"


def test_unpublished_series_are_reported_not_fetched() -> None:
    reqs, skipped = native_series(["NL"])
    assert all(r.source_id in {"eurostat", "ecb", "oecd"} for r in reqs)
    assert "NL/cli: not_published" in skipped
    assert {r.series_key for r in reqs if r.source_id == "oecd"} == {
        "NLD.M.BCICP.IX._Z.AA.IX._Z.H",
        "NLD.M.CCICP.IX._Z.AA.IX._Z.H",
    }
    us, _ = native_series(["US"], ["oecd"])
    assert {r.indicator_ids for r in us} == {
        ("cli",),
        ("business_confidence",),
        ("consumer_confidence",),
    }


def test_us_series_come_from_fred_only() -> None:
    reqs, _ = native_series(["US"], ["fred"])
    assert {r.dataset for r in reqs} >= {"GDPC1", "CPIAUCSL", "UNRATE", "USREC"}
    assert all(r.geo == "US" for r in reqs)


# --- quality rules ----------------------------------------------------------------------------


def test_clean_quarterly_series_passes() -> None:
    rules = _by_rule(_result(Q_REQ, [("2026-Q2", 100.0, None), ("2026-Q3", 101.0, None)]))
    assert rules["non_empty"][0] == "pass"
    assert rules["gaps"][0] == "pass"
    assert rules["freshness"][0] == "pass"
    assert rules["plausible_range"][0] == "pass"
    assert "source_flags" not in rules


def test_empty_series_fails() -> None:
    rules = _by_rule(_result(Q_REQ, []))
    assert rules["non_empty"][0] == "fail"


def test_duplicates_fail_and_internal_gaps_warn() -> None:
    dup = _by_rule(_result(M_REQ, [("2026-09", 6.0, None), ("2026-09", 6.1, None)]))
    assert dup["unique_periods"][0] == "fail"
    gap = _by_rule(_result(M_REQ, [("2026-06", 6.0, None), ("2026-09", 6.1, None)]))
    status, detail = gap["gaps"]
    assert status == "warn"
    assert "2 missing period(s)" in detail
    assert "2026-07, 2026-08" in detail


def test_stale_series_warns() -> None:
    rules = _by_rule(_result(M_REQ, [("2025-12", 6.0, None)]))
    assert rules["freshness"][0] == "warn"


def test_non_positive_levels_and_absurd_rates_warn() -> None:
    assert _by_rule(_result(Q_REQ, [("2026-Q3", 0.0, None)]))["plausible_range"][0] == "warn"
    assert _by_rule(_result(M_REQ, [("2026-10", 900.0, None)]))["plausible_range"][0] == "warn"


def test_source_flags_and_warnings_are_surfaced() -> None:
    result = _result(Q_REQ, [("2026-Q2", 100.0, "p"), ("2026-Q3", 101.0, "p")])
    result.warnings.append("1 missing value(s) skipped")
    rules = _by_rule(result)
    assert "2 observation(s) flagged" in rules["source_flags"][1]
    assert rules["source_warning"] == ("warn", "1 missing value(s) skipped")


def test_normal_release_lag_is_not_stale() -> None:
    # Quarterly government debt for Q2 is published ~t+115 days; on 2026-11-09 it is the latest.
    debt = SeriesRequest("eurostat", "gov_10q_ggdebt", "k", "DE", "quarterly", "% of GDP")
    assert _by_rule(_result(debt, [("2026-Q2", 62.0, None)]))["freshness"][0] == "pass"
    # A quarter more than 150 days past its end is a missed release.
    assert _by_rule(_result(debt, [("2026-Q1", 62.0, None)]))["freshness"][0] == "warn"


def test_sdmx_normal_status_is_not_a_flag() -> None:
    rate = SeriesRequest("ecb", "FM", "k", "EA", "event", "% per annum")
    rules = _by_rule(_result(rate, [("2026-06-17", 2.25, "A"), ("2026-09-16", 2.5, "A")]))
    assert "source_flags" not in rules
    mixed = _by_rule(_result(Q_REQ, [("2026-Q2", 100.0, "A"), ("2026-Q3", 101.0, "p")]))
    assert mixed["source_flags"][1].startswith("1 observation(s) flagged by the source: p")
