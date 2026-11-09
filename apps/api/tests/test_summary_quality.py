"""Country summary (KPI tiles), data-quality inventory and raw CSV export over real fixtures."""

from __future__ import annotations

import csv
import io
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from macropulse_api.routers.summary import kpi_value
from macropulse_economics.connectors import ConnectorError, FetchResult, SeriesRequest
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.indicators import get_indicator

from .fixture_sources import DE_GDP_ID, offline_fetcher, sync_fixtures

DE_Q = {"2025-Q2": 914518.6, "2025-Q3": 914257.8, "2025-Q4": 916692.1, "2026-Q1": 920604.4}
DE_Q |= {"2026-Q2": 923560.3, "2026-Q3": 925646.9}


def _growth(cur: str, prev: str) -> float:
    return (DE_Q[cur] / DE_Q[prev] - 1) * 100


@pytest.fixture
def synced(app: FastAPI, client: TestClient) -> TestClient:
    sync_fixtures(app, offline_fetcher())
    return client


def _kpis(client: TestClient, iso: str, **params: str) -> dict[str, dict]:
    r = client.get(f"/api/countries/{iso}/summary", params=params)
    assert r.status_code == 200, r.text
    return {k["indicator"]["id"]: k for k in r.json()["kpis"]}


# --- summary ----------------------------------------------------------------------------------


def test_latest_kpis_carry_value_change_flag_and_provenance(synced: TestClient) -> None:
    body = synced.get("/api/countries/de/summary").json()
    assert body["country"] == "DE"
    assert body["as_of"] is None
    assert "revised data" in body["data_basis"]
    assert body["freshness"] is not None
    kpis = {k["indicator"]["id"]: k for k in body["kpis"]}
    assert list(kpis) == ["real_gdp_qoq", "inflation_yoy", "unemployment_rate", "policy_rate"]

    gdp = kpis["real_gdp_qoq"]
    assert gdp["status"] == "ok"
    assert gdp["period"] == "2026-Q3"
    assert gdp["value"] == pytest.approx(_growth("2026-Q3", "2026-Q2"), abs=1e-6)
    assert gdp["previous_period"] == "2026-Q2"
    assert gdp["change"] == pytest.approx(
        _growth("2026-Q3", "2026-Q2") - _growth("2026-Q2", "2026-Q1"), abs=1e-6
    )
    assert gdp["source_flag"] == "p"
    assert gdp["unit"] == "%"
    assert gdp["provenance"]["series_id"] == DE_GDP_ID
    assert gdp["provenance"]["request_url"] == "https://ec.europa.eu/x?geo=DE"

    rate = kpis["policy_rate"]
    assert (rate["value"], rate["period"], rate["previous_value"]) == (2.5, "2026-09-16", 2.25)
    assert rate["change"] == pytest.approx(0.25)
    assert rate["stale"] is False  # event-dated: no age limit
    assert "Shared euro area" in rate["scope_note"]


def test_mapped_but_unsynced_kpis_say_so_without_a_number(synced: TestClient) -> None:
    kpis = _kpis(synced, "DE")
    for ind in ("inflation_yoy", "unemployment_rate"):
        assert kpis[ind]["status"] == "no_data"
        assert kpis[ind]["value"] is None
        assert "data-sync" in kpis[ind]["reason"]
    us = _kpis(synced, "US")
    assert {k["status"] for k in us.values()} == {"no_data"}


def test_as_of_cuts_off_later_periods_and_labels_the_basis(synced: TestClient) -> None:
    body = synced.get("/api/countries/DE/summary", params={"as_of": "2026-Q1"}).json()
    assert body["cutoff"] == "2026-03-31"
    assert "vintages" in body["data_basis"]
    kpis = {k["indicator"]["id"]: k for k in body["kpis"]}
    assert kpis["real_gdp_qoq"]["period"] == "2026-Q1"
    assert kpis["real_gdp_qoq"]["value"] == pytest.approx(_growth("2026-Q1", "2025-Q4"), abs=1e-6)
    assert kpis["real_gdp_qoq"]["days_since_period_end"] == 0
    assert kpis["real_gdp_qoq"]["stale"] is False
    assert (kpis["policy_rate"]["value"], kpis["policy_rate"]["period"]) == (2.0, "2025-06-11")
    assert kpis["policy_rate"]["days_since_period_end"] == 293


def test_as_of_before_any_derivable_value_is_no_data(synced: TestClient) -> None:
    gdp = _kpis(synced, "DE", as_of="2025-Q2")["real_gdp_qoq"]
    assert gdp["status"] == "no_data"
    assert "2025-06-30" in gdp["reason"]
    assert gdp["provenance"] is not None  # the series exists; it just starts later


@pytest.mark.parametrize(
    ("as_of", "code"), [("2099-Q1", "invalid_as_of"), ("2026Q1", "validation_error")]
)
def test_invalid_as_of(synced: TestClient, as_of: str, code: str) -> None:
    r = synced.get("/api/countries/DE/summary", params={"as_of": as_of})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == code


def test_unsupported_country_summary(synced: TestClient) -> None:
    r = synced.get("/api/countries/XX/summary")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unsupported_country"


def test_unpublished_indicator_is_unavailable_with_the_source_note(app: FastAPI) -> None:
    cli = get_indicator("cli")
    assert cli is not None
    with app.state.sessionmaker() as session:
        k = kpi_value(session, "NL", cli, date(2026, 11, 9))
    assert k.status == "unavailable"
    assert k.value is None
    assert k.reason


# --- data quality -----------------------------------------------------------------------------


def test_country_data_quality_lists_every_series_behind_the_country(synced: TestClient) -> None:
    body = synced.get("/api/countries/DE/data-quality").json()
    by_id = {i["series_id"]: i for i in body["items"]}
    assert len(by_id) == 5  # GDP, HICP, unemployment, debt + the shared ECB rate
    gdp = by_id[DE_GDP_ID]
    assert gdp["health"] == "pass"
    assert gdp["observations"] == 6
    assert (gdp["first_period"], gdp["last_period"]) == ("2025-Q2", "2026-Q3")
    assert gdp["indicators"] == ["real_gdp_qoq", "real_gdp_yoy"]
    assert gdp["source_updated_at"] == "2026-11-05T23:00:00+0100"
    assert {q["rule"] for q in gdp["quality"]} >= {"non_empty", "gaps", "freshness", "unit_echo"}
    ecb = next(i for i in body["items"] if i["source_id"] == "ecb")
    assert ecb["countries"] == ["BE", "DE", "FR", "NL"]
    hicp = next(i for i in body["items"] if i["dataset"] == "prc_hicp_minr")
    assert hicp["health"] == "fail"  # the fixture fetch refused it
    assert hicp["observations"] == 0
    assert body["counts"]["fail"] >= 1


def test_global_inventory_reports_never_synced_series(synced: TestClient) -> None:
    body = synced.get("/api/data-quality").json()
    assert len(body["items"]) == 24
    fred = [i for i in body["items"] if i["source_id"] == "fred"]
    assert fred
    assert {i["health"] for i in fred} == {"not_synced"}
    assert sum(body["counts"].values()) == 24


def test_a_failed_latest_sync_is_visible_while_older_rows_remain(
    app: FastAPI, synced: TestClient
) -> None:
    def offline(_f: Fetcher, req: SeriesRequest) -> FetchResult:
        raise ConnectorError("ec.europa.eu: request failed after 4 attempt(s) (ConnectError)")

    sync_fixtures(app, offline_fetcher(), sources=["eurostat"], countries=["DE"], fetch=offline)
    item = next(
        i
        for i in synced.get("/api/countries/DE/data-quality").json()["items"]
        if i["series_id"] == DE_GDP_ID
    )
    assert item["health"] == "fail"
    assert item["observations"] == 6
    assert "ConnectError" in item["quality"][0]["detail"]


# --- CSV export -------------------------------------------------------------------------------


def test_raw_csv_export_has_provenance_on_every_row(synced: TestClient) -> None:
    item = next(
        i
        for i in synced.get("/api/countries/DE/data-quality").json()["items"]
        if i["series_id"] == DE_GDP_ID
    )
    r = synced.get(item["export_path"])
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(rows) == 6
    assert rows[0]["period"] == "2025-Q2"
    assert float(rows[0]["value"]) == DE_Q["2025-Q2"]
    assert rows[0]["source_flag"] == "p"
    assert rows[0]["source_url"] == "https://ec.europa.eu/x?geo=DE"
    assert rows[0]["attribution"]
    assert r.text.endswith("\r\n")


@pytest.mark.parametrize(
    ("series_id", "status", "code"),
    [
        ("eurostat:nonexistent:x:DE", 404, "series_not_found"),
        ("eurostat:prc_hicp_minr:freq=M, unit=RCH_A, coicop18=TOTAL:DE", 503, "data_not_synced"),
    ],
)
def test_csv_export_errors(synced: TestClient, series_id: str, status: int, code: str) -> None:
    r = synced.get("/api/observations/export", params={"series_id": series_id})
    assert r.status_code == status
    assert r.json()["error"]["code"] == code
