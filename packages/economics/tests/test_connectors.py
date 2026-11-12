"""Connector parsers and HTTP behaviour, against real captured responses (see fixtures/README.md).

No network: live checks live in test_live_sources.py behind MACROPULSE_LIVE_TESTS=1.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from macropulse_economics.connectors import ConnectorError, SeriesRequest, ecb, eurostat, fred
from macropulse_economics.connectors.http import (
    HOST_MIN_INTERVAL_S,
    MIN_INTERVAL_S,
    RATE_LIMIT_WAIT_S,
    Fetcher,
    make_client,
)
from macropulse_economics.connectors.registry import fetch_series

FIXTURES = Path(__file__).parent / "fixtures"

DE_GDP = SeriesRequest(
    "eurostat",
    "namq_10_gdp",
    "freq=Q, unit=CLV20_MNAC, s_adj=SCA, na_item=B1GQ",
    "DE",
    "quarterly",
    "Chain-linked volumes (2020), million units of national currency",
    "SCA",
)
FR_HICP = SeriesRequest(
    "eurostat", "prc_hicp_minr", "freq=M, unit=RCH_A, coicop18=TOTAL", "FR", "monthly", "%"
)
ECB_DFR = SeriesRequest("ecb", "FM", "B.U2.EUR.4F.KR.DFR.LEV", "EA", "event", "% per annum")
US_GDP = SeriesRequest("fred", "GDPC1", "GDPC1", "US", "quarterly", "Billions of chained dollars")


def _json(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data


def _text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class Recorder:
    def __init__(self) -> None:
        self.sleeps: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.sleeps.append(seconds)


def _fetcher(handler: Any, recorder: Recorder | None = None) -> Fetcher:
    client = make_client(transport=httpx.MockTransport(handler))
    return Fetcher(client, retries=2, backoff_s=1.0, sleep=recorder or Recorder())


# --- Eurostat JSON-stat -----------------------------------------------------------------------


def test_eurostat_parses_real_gdp_levels_with_flags_and_unit() -> None:
    obs, unit, updated = eurostat.parse_jsonstat(
        _json("eurostat_namq_10_gdp_DE_last6.json"), DE_GDP
    )
    assert [o.period for o in obs] == [
        "2025-Q2",
        "2025-Q3",
        "2025-Q4",
        "2026-Q1",
        "2026-Q2",
        "2026-Q3",
    ]
    assert obs[0].value == 914518.6
    assert {o.obs_status for o in obs} == {"p"}  # Eurostat marks them provisional
    assert unit == "Chain linked volumes (2020), million units of national currency"
    assert updated == "2026-11-05T23:00:00+0100"


def test_eurostat_keeps_flags_only_where_published() -> None:
    obs, _, _ = eurostat.parse_jsonstat(_json("eurostat_prc_hicp_minr_FR_last4.json"), FR_HICP)
    assert [(o.period, o.value, o.obs_status) for o in obs] == [
        ("2026-07", 2.4, None),
        ("2026-08", 2.6, None),
        ("2026-09", 3.4, None),
        ("2026-10", 3.8, "e"),
    ]


def test_eurostat_missing_values_stay_missing() -> None:
    payload = _json("eurostat_namq_10_gdp_DE_last6.json")
    del payload["value"]["2"]
    obs, _, _ = eurostat.parse_jsonstat(payload, DE_GDP)
    assert "2025-Q4" not in [o.period for o in obs]
    assert len(obs) == 5


def test_eurostat_rejects_a_filter_that_selects_several_series() -> None:
    payload = copy.deepcopy(_json("eurostat_namq_10_gdp_DE_last6.json"))
    payload["size"][4] = 2  # two geos
    with pytest.raises(ConnectorError, match="several series"):
        eurostat.parse_jsonstat(payload, DE_GDP)


def test_eurostat_error_payload_and_non_jsonstat_are_errors() -> None:
    with pytest.raises(ConnectorError, match="Eurostat error"):
        eurostat.parse_jsonstat({"error": [{"status": 400, "label": "bad"}]}, DE_GDP)
    with pytest.raises(ConnectorError, match="not JSON-stat"):
        eurostat.parse_jsonstat({"hello": 1}, DE_GDP)


def test_eurostat_filters_parse_and_reject_malformed_keys() -> None:
    assert eurostat.parse_filters("freq=Q, unit=CLV20_MNAC") == {"freq": "Q", "unit": "CLV20_MNAC"}
    with pytest.raises(ConnectorError):
        eurostat.parse_filters("freq=Q, broken")


def test_eurostat_fetch_sends_filters_geo_and_records_provenance() -> None:
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, json=_json("eurostat_namq_10_gdp_DE_last6.json"))

    result = eurostat.fetch(_fetcher(handler), DE_GDP)
    params = dict(seen[0].params)
    assert seen[0].path.endswith("/data/namq_10_gdp")
    assert params == {
        "freq": "Q",
        "unit": "CLV20_MNAC",
        "s_adj": "SCA",
        "na_item": "B1GQ",
        "geo": "DE",
        "lang": "EN",
    }
    assert result.url == str(seen[0])
    assert result.source_updated_at == "2026-11-05T23:00:00+0100"
    assert result.retrieved_at.tzinfo is not None
    assert len(result.observations) == 6


# --- ECB SDMX CSV -----------------------------------------------------------------------------


def test_ecb_parses_event_dated_policy_rate() -> None:
    obs, _unit = ecb.parse_csv(_text("ecb_FM_DFR_last4.csv"), ECB_DFR)
    assert [(o.period, o.value) for o in obs] == [
        ("2025-04-23", 2.25),
        ("2025-06-11", 2.0),
        ("2026-06-17", 2.25),
        ("2026-09-16", 2.5),
    ]


def test_ecb_rejects_an_unexpected_series_key() -> None:
    other = SeriesRequest("ecb", "FM", "B.U2.EUR.4F.KR.MRR_FR.LEV", "EA", "event", "%")
    with pytest.raises(ConnectorError, match="unexpected series"):
        ecb.parse_csv(_text("ecb_FM_DFR_last4.csv"), other)


def test_ecb_rejects_empty_and_malformed_csv() -> None:
    with pytest.raises(ConnectorError, match="empty"):
        ecb.parse_csv("KEY,TIME_PERIOD,OBS_VALUE\n", ECB_DFR)
    with pytest.raises(ConnectorError, match="TIME_PERIOD"):
        ecb.parse_csv("a,b\n1,2\n", ECB_DFR)


# --- FRED -------------------------------------------------------------------------------------


def test_fred_parses_quarter_start_dates_into_quarters() -> None:
    obs, missing = fred.parse_csv(_text("fred_GDPC1_2024.csv"), US_GDP)
    assert missing == 0
    assert obs[0].period == "2024-Q1"
    assert obs[-1].period == "2026-Q3"
    assert obs[-1].value == 24611.077
    assert len(obs) == 11


def test_fred_missing_marker_is_skipped_and_counted() -> None:
    text = "observation_date,GDPC1\n2024-01-01,1.0\n2024-04-01,.\n2024-07-01,3.0\n"
    obs, missing = fred.parse_csv(text, US_GDP)
    assert [o.period for o in obs] == ["2024-Q1", "2024-Q3"]
    assert missing == 1


def test_fred_rejects_a_different_series_header() -> None:
    with pytest.raises(ConnectorError, match="unexpected CSV header"):
        fred.parse_csv("observation_date,UNRATE\n2024-01-01,4.0\n", US_GDP)


def test_fred_fetch_reports_missing_values_as_a_warning() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["id"] == "GDPC1"
        return httpx.Response(200, text="observation_date,GDPC1\n2024-01-01,1.0\n2024-04-01,.\n")

    result = fred.fetch(_fetcher(handler), US_GDP)
    assert len(result.observations) == 1
    assert result.warnings == ["1 missing value(s) marked '.' by FRED were skipped"]


def test_registry_rejects_sources_without_a_connector() -> None:
    world_bank = SeriesRequest("worldbank", "WDI", "X", "DE", "annual", "%")
    with pytest.raises(ConnectorError, match="No connector"):
        fetch_series(_fetcher(lambda r: httpx.Response(200)), world_bank)


# --- HTTP retries -----------------------------------------------------------------------------


def test_fetcher_retries_server_errors_with_backoff() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503 if calls["n"] < 3 else 200, text="ok")

    rec = Recorder()
    response = _fetcher(handler, rec).get("https://example.test/data")
    assert response.status_code == 200
    assert calls["n"] == 3
    backoffs = [s for s in rec.sleeps if s >= 1.0]
    assert backoffs == [1.0, 2.0]  # exponential


def test_fetcher_honours_retry_after_on_429() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200)

    rec = Recorder()
    _fetcher(handler, rec).get("https://example.test/data")
    assert 7.0 in rec.sleeps


def test_fetcher_waits_out_a_rate_limit_without_retry_after() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429) if calls["n"] == 1 else httpx.Response(200)

    rec = Recorder()
    _fetcher(handler, rec).get("https://example.test/data")
    assert RATE_LIMIT_WAIT_S in rec.sleeps
    assert calls["n"] == 2


def test_rate_limited_hosts_are_spaced_wider() -> None:
    rec = Recorder()
    fetcher = _fetcher(lambda r: httpx.Response(200), rec)
    fetcher.get("https://sdmx.oecd.org/public/rest/data/a")
    fetcher.get("https://sdmx.oecd.org/public/rest/data/b")
    fetcher.get("https://example.test/a")
    fetcher.get("https://example.test/b")
    assert rec.sleeps[0] > HOST_MIN_INTERVAL_S["sdmx.oecd.org"] - 0.5
    assert rec.sleeps[1] <= MIN_INTERVAL_S


def test_fetcher_does_not_retry_client_errors() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404)

    with pytest.raises(ConnectorError, match="HTTP 404"):
        _fetcher(handler).get("https://example.test/data")
    assert calls["n"] == 1


def test_fetcher_gives_up_after_transport_errors_with_a_safe_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(ConnectorError) as info:
        _fetcher(handler).get("https://example.test/data?api_key=secret")
    assert "3 attempt(s)" in str(info.value)
    assert "ConnectError" in str(info.value)
    assert "secret" not in str(info.value)
