"""ALFRED vintages: sync into the vintage tables, revisions endpoint, key handling. No network."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from macropulse_api.models import VintageObservation as VintageRow
from macropulse_api.models import VintageSeries
from macropulse_api.services.vintages import sync_vintages, technical_signals, vintage_requests
from macropulse_economics.connectors import ConnectorError, SeriesRequest
from macropulse_economics.connectors.alfred import VintageFetch
from macropulse_economics.connectors.alfred import VintageObservation as V
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.transforms import Transform
from macropulse_economics.vintages import revision_history

KEY = "0123456789abcdef0123456789abcdef"  # fake test value

ROWS: dict[str, list[V]] = {
    "GDPC1": [
        V("2008-Q1", 100.0, date(2008, 4, 30), date(2008, 5, 28)),
        V("2008-Q1", 100.5, date(2008, 5, 29), None),
        V("2008-Q2", 101.0, date(2008, 7, 31), date(2008, 8, 27)),
        V("2008-Q2", 100.0, date(2008, 8, 28), None),
        V("2008-Q3", 100.0, date(2008, 10, 30), None),
    ],
    "UNRATE": [
        V("2020-04", 14.7, date(2020, 5, 8), date(2020, 6, 4)),
        V("2020-04", 14.8, date(2020, 6, 5), None),
    ],
    "CPIAUCSL": [V("2020-01", 258.0, date(2020, 2, 13), None)],
}


def fake_fetch(_fetcher: Fetcher, request: SeriesRequest, key: str | None) -> VintageFetch:
    assert key == KEY
    return VintageFetch(
        request=request,
        observations=ROWS[request.dataset],
        url=f"https://api.stlouisfed.org/fred/series/observations?series_id={request.dataset}"
        f"&api_key={key}",
        retrieved_at=datetime(2026, 11, 12, 8, 0, tzinfo=UTC),
    )


def sync(app: FastAPI, fetch: object = fake_fetch) -> None:
    report = sync_vintages(app.state.sessionmaker, None, KEY, fetch=fetch)  # type: ignore[arg-type]
    assert report.outcomes


def test_only_us_gdp_cpi_and_unemployment_are_fetched() -> None:
    assert sorted(r.dataset for r in vintage_requests()) == ["CPIAUCSL", "GDPC1", "UNRATE"]


def test_before_sync_the_endpoint_says_how_to_sync(client: TestClient) -> None:
    r = client.get("/api/vintages/revisions", params={"country": "US", "indicator": "real_gdp_qoq"})
    assert r.status_code == 503
    body = r.json()["error"]
    assert body["code"] == "vintages_not_synced"
    assert "vintages-sync" in body["message"]
    assert body["details"]["fred_api_key_configured"] is False


@pytest.mark.parametrize(
    ("country", "indicator", "code"),
    [
        ("DE", "real_gdp_qoq", "vintages_not_available"),
        ("US", "policy_rate", "unsupported_indicator"),
    ],
)
def test_unsupported_requests_are_422(
    client: TestClient, country: str, indicator: str, code: str
) -> None:
    r = client.get("/api/vintages/revisions", params={"country": country, "indicator": indicator})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == code


def test_revisions_compare_first_release_with_the_current_vintage(
    app: FastAPI, client: TestClient
) -> None:
    sync(app)
    r = client.get("/api/vintages/revisions", params={"country": "us", "indicator": "real_gdp_qoq"})
    assert r.status_code == 200
    body = r.json()
    assert [p["period"] for p in body["points"]] == ["2008-Q2", "2008-Q3"]
    q2 = body["points"][0]
    assert q2["first_published"] == "2008-07-31"
    assert q2["first_value"] == pytest.approx(0.497512, abs=1e-6)
    assert q2["latest_value"] == pytest.approx(-0.497512, abs=1e-6)
    assert body["summary"]["sign_changes"] == ["2008-Q2"]
    assert body["revision_unit"] == "pp"
    assert body["series"]["vintages"] == 5  # distinct publication dates
    assert body["series"]["first_vintage"] == "2008-04-30"


def test_identity_indicator_revisions(app: FastAPI, client: TestClient) -> None:
    sync(app)
    body = client.get(
        "/api/vintages/revisions", params={"country": "US", "indicator": "unemployment_rate"}
    ).json()
    (point,) = body["points"]
    assert point["first_value"] == 14.7
    assert point["revision"] == pytest.approx(0.1)


def test_the_key_is_never_stored_or_served(app: FastAPI, client: TestClient) -> None:
    sync(app)
    with app.state.sessionmaker() as s:
        urls = list(s.scalars(select(VintageSeries.source_url)))
    assert urls and all(KEY not in u and "api_key=REDACTED" in u for u in urls)
    body = client.get(
        "/api/vintages/revisions", params={"country": "US", "indicator": "inflation_yoy"}
    ).text
    assert KEY not in body


def test_a_failed_refresh_keeps_the_stored_history_and_hides_the_key(app: FastAPI) -> None:
    sync(app)

    def failing(_f: Fetcher, request: SeriesRequest, key: str | None) -> VintageFetch:
        raise ConnectorError(f"api.stlouisfed.org: rejected {key}")

    report = sync_vintages(app.state.sessionmaker, None, KEY, fetch=failing)  # type: ignore[arg-type]
    assert all(not o.ok for o in report.outcomes)
    assert all(KEY not in (o.error or "") for o in report.outcomes)
    with app.state.sessionmaker() as s:
        assert s.scalar(select(func.count()).select_from(VintageRow)) == 8


def test_a_resync_replaces_rather_than_duplicates(app: FastAPI) -> None:
    sync(app)
    sync(app)
    with app.state.sessionmaker() as s:
        assert s.scalar(select(func.count()).select_from(VintageRow)) == 8
        assert s.scalar(select(func.count()).select_from(VintageSeries)) == 3


def test_periods_published_before_the_archive_are_flagged_and_left_out(
    app: FastAPI, client: TestClient
) -> None:
    sync(app)
    body = client.get(
        "/api/vintages/revisions", params={"country": "US", "indicator": "real_gdp_qoq"}
    ).json()
    assert body["archive_start"] == "2008-04-30"
    assert [p["first_release"] for p in body["points"]] == [True, True]
    # unemployment: the only period appears in the very first stored vintage -> not a first release
    un = client.get(
        "/api/vintages/revisions", params={"country": "US", "indicator": "unemployment_rate"}
    ).json()
    assert un["points"][0]["first_release"] is False
    assert un["summary"]["count"] == 0
    assert un["technical_signals"] == []


def test_technical_signal_as_first_known_versus_today(app: FastAPI) -> None:
    rows = [
        V("2022-Q1", 100.0, date(2022, 1, 27), None),  # archive start
        V("2022-Q2", 99.0, date(2022, 4, 28), None),  # -1.0 %, unrevised
        V("2022-Q3", 98.5, date(2022, 7, 28), date(2022, 9, 28)),  # first -0.505 %
        V("2022-Q3", 99.5, date(2022, 9, 29), None),  # revised to +0.505 %
    ]

    qoq = Transform("growth", 1)
    points = [p for p in revision_history(rows, qoq) if p.first_published > date(2022, 1, 27)]
    (signal,) = technical_signals(rows, points, qoq)
    assert signal["period"] == "2022-Q3"
    assert signal["as_first_known"] is True
    assert signal["in_latest_data"] is False


def test_back_filled_history_is_not_a_first_release(app: FastAPI, client: TestClient) -> None:
    rows = [
        *ROWS["GDPC1"],
        # a later vintage adds 1990 quarters: published 18 years after they ended
        V("1990-Q1", 50.0, date(2008, 7, 31), None),
        V("1990-Q2", 49.0, date(2008, 7, 31), None),
    ]

    def fetch(_f: Fetcher, request: SeriesRequest, key: str | None) -> VintageFetch:
        result = fake_fetch(_f, request, key)
        if request.dataset == "GDPC1":
            result.observations = rows
        return result

    sync(app, fetch)
    body = client.get(
        "/api/vintages/revisions", params={"country": "US", "indicator": "real_gdp_qoq"}
    ).json()
    flags = {p["period"]: p["first_release"] for p in body["points"]}
    assert flags["1990-Q2"] is False
    assert body["summary"]["count"] == 2  # only 2008-Q2 and 2008-Q3
    assert all(s["period"] != "1990-Q2" for s in body["technical_signals"])
