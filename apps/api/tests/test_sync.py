"""`data-sync` service and `GET /api/indicators`, driven by real captured source responses.

The fake fetch serves the fixtures in packages/economics/tests/fixtures (DE real GDP, FR HICP, the
ECB deposit-facility rate) and fails every other series, exactly as an unreachable source would.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from macropulse_api.models import IngestionRun, Observation, QualityCheck
from macropulse_api.services.sync import SyncReport
from macropulse_economics.connectors import (
    ConnectorError,
    FetchedObservation,
    FetchResult,
    SeriesRequest,
)
from macropulse_economics.connectors.http import Fetcher

from .fixture_sources import DE_GDP_ID, offline_fetcher, sync_fixtures


@pytest.fixture
def fetcher() -> Fetcher:
    return offline_fetcher()


def _sync(app: FastAPI, fetcher: Fetcher, **kwargs: object) -> SyncReport:
    return sync_fixtures(app, fetcher, **kwargs)


def test_sync_records_runs_rows_and_explicit_partial_failures(
    app: FastAPI, fetcher: Fetcher
) -> None:
    report = _sync(app, fetcher)
    statuses = {source: status for source, (_run, status) in report.runs.items()}
    assert statuses == {"ecb": "succeeded", "eurostat": "partial"}
    ok = {o.series_id: o.rows for o in report.outcomes if o.ok}
    assert ok[DE_GDP_ID] == 6
    assert sum(ok.values()) == 6 + 4 + 4
    failed = [o for o in report.outcomes if not o.ok]
    assert failed
    assert all("not captured" in (o.error or "") for o in failed)

    with app.state.sessionmaker() as s:
        assert s.scalar(select(func.count()).select_from(Observation)) == 14
        run = s.get(IngestionRun, report.runs["eurostat"][0])
        assert run is not None
        assert run.rows_upserted == 10
        assert run.finished_at is not None
        assert "not captured" in (run.error_summary or "")
        rules = set(s.scalars(select(QualityCheck.rule).where(QualityCheck.series_id == DE_GDP_ID)))
        assert {"non_empty", "gaps", "freshness", "source_flags", "unit_echo"} <= rules
        fetch_fails = s.scalars(select(QualityCheck).where(QualityCheck.rule == "fetch")).all()
        assert len(fetch_fails) == len(failed)
        gdp = s.scalars(select(Observation).where(Observation.series_id == DE_GDP_ID)).first()
        assert gdp is not None
        assert gdp.obs_status == "p"
        assert gdp.source_updated_at == "2026-11-05T23:00:00+0100"
        assert gdp.retrieved_at is not None


def test_resync_is_idempotent_and_moves_provenance_to_the_new_run(
    app: FastAPI, fetcher: Fetcher
) -> None:
    first = _sync(app, fetcher)
    second = _sync(app, fetcher)
    with app.state.sessionmaker() as s:
        assert s.scalar(select(func.count()).select_from(Observation)) == 14
        run_ids = set(s.scalars(select(Observation.ingestion_run_id)))
    assert run_ids == {second.runs["eurostat"][0], second.runs["ecb"][0]}
    assert first.runs["eurostat"][0] != second.runs["eurostat"][0]


def test_run_with_only_failures_is_failed_and_reported(
    app: FastAPI, fetcher: Fetcher, client: TestClient
) -> None:
    def offline(_f: Fetcher, req: SeriesRequest) -> FetchResult:
        raise ConnectorError("ec.europa.eu: request failed after 4 attempt(s) (ConnectError)")

    report = _sync(app, fetcher, sources=["eurostat"], fetch=offline)
    assert report.runs["eurostat"][1] == "failed"
    eurostat_status = next(
        s for s in client.get("/api/sources/status").json()["items"] if s["id"] == "eurostat"
    )
    assert eurostat_status["status"] == "failed"
    assert eurostat_status["last_success_at"] is None


def test_series_failing_a_quality_rule_is_not_stored(app: FastAPI, fetcher: Fetcher) -> None:
    def duplicated(_f: Fetcher, req: SeriesRequest) -> FetchResult:
        obs = [FetchedObservation("2026-Q3", 1.0), FetchedObservation("2026-Q3", 2.0)]
        return FetchResult(req, obs, "https://example.test", datetime.now(UTC))

    report = _sync(app, fetcher, sources=["eurostat"], countries=["DE"], fetch=duplicated)
    assert report.runs["eurostat"][1] == "failed"
    assert all("Duplicate periods" in (o.error or "") for o in report.outcomes)
    with app.state.sessionmaker() as s:
        assert s.scalar(select(func.count()).select_from(Observation)) == 0


def test_unexpected_errors_are_contained_with_a_safe_message(
    app: FastAPI, fetcher: Fetcher
) -> None:
    def broken(_f: Fetcher, req: SeriesRequest) -> FetchResult:
        raise KeyError("internal detail")

    report = _sync(app, fetcher, sources=["ecb"], countries=["DE"], fetch=broken)
    assert report.outcomes[0].error == "unexpected KeyError"


# --- what the API serves after a sync ---------------------------------------------------------


@pytest.fixture
def synced(app: FastAPI, fetcher: Fetcher, client: TestClient) -> TestClient:
    _sync(app, fetcher)
    return client


def test_real_gdp_growth_is_derived_only_from_consecutive_published_quarters(
    synced: TestClient,
) -> None:
    r = synced.get("/api/indicators", params={"country": "DE", "indicator": "real_gdp_qoq"})
    assert r.status_code == 200
    body = r.json()
    periods = [p["period"] for p in body["points"]]
    assert periods == ["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2", "2026-Q3"]
    assert body["points"][0]["value"] == pytest.approx((914257.8 / 914518.6 - 1) * 100, abs=1e-6)
    assert body["unit"] == "%"
    assert "Quarter-on-quarter" in body["transform"]
    prov = body["provenance"]
    assert prov["dataset"] == "namq_10_gdp"
    assert prov["native_observations"] == 6
    assert prov["request_url"] == "https://ec.europa.eu/x?geo=DE"
    assert prov["retrieved_at"] is not None
    assert prov["source_updated_at"] == "2026-11-05T23:00:00+0100"
    assert {q["rule"] for q in body["quality"]} >= {"freshness", "unit_echo"}
    assert body["truncated"] is False


def test_year_on_year_needs_four_quarters_of_history(synced: TestClient) -> None:
    body = synced.get("/api/indicators?country=DE&indicator=real_gdp_yoy").json()
    assert [p["period"] for p in body["points"]] == ["2026-Q2", "2026-Q3"]


def test_published_rates_are_shown_as_published(synced: TestClient) -> None:
    body = synced.get("/api/indicators?country=FR&indicator=inflation_yoy").json()
    assert [(p["period"], p["value"]) for p in body["points"]][-1] == ("2026-10", 3.8)
    assert body["transform"] == "As published by the source."


def test_euro_area_rate_is_served_for_members_with_its_scope(synced: TestClient) -> None:
    body = synced.get("/api/indicators?country=DE&indicator=policy_rate").json()
    assert body["points"][-1] == {"period": "2026-09-16", "value": 2.5}
    assert body["provenance"]["series_id"].endswith(":EA")
    assert "euro" in body["scope_note"].lower()


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"start": "2026-Q1"}, ["2026-Q1", "2026-Q2", "2026-Q3"]),
        ({"end": "2025"}, ["2025-Q3", "2025-Q4"]),
        ({"start": "2025-10", "end": "2026-02"}, ["2025-Q4", "2026-Q1"]),
    ],
)
def test_period_bounds(synced: TestClient, params: dict[str, str], expected: list[str]) -> None:
    query = {"country": "DE", "indicator": "real_gdp_qoq", **params}
    body = synced.get("/api/indicators", params=query).json()
    assert [p["period"] for p in body["points"]] == expected


@pytest.mark.parametrize(
    ("params", "status", "code"),
    [
        ({"country": "XX", "indicator": "real_gdp_qoq"}, 422, "unsupported_country"),
        ({"country": "DE", "indicator": "gdp_magic"}, 422, "unsupported_indicator"),
        (
            {"country": "DE", "indicator": "real_gdp_qoq", "start": "2026", "end": "2025"},
            422,
            "invalid_range",
        ),
        ({"country": "DE", "indicator": "real_gdp_qoq", "start": "2026-13"}, 422, "invalid_range"),
        ({"country": "DE", "indicator": "real_gdp_qoq", "start": "26"}, 422, "validation_error"),
        ({"country": "NL", "indicator": "cli"}, 404, "indicator_unavailable"),
        ({"country": "DE", "indicator": "yield_spread"}, 404, "indicator_unavailable"),
        ({"country": "DE", "indicator": "unemployment_rate"}, 503, "data_not_synced"),
    ],
)
def test_errors_follow_the_contract(
    synced: TestClient, params: dict[str, str], status: int, code: str
) -> None:
    r = synced.get("/api/indicators", params=params)
    assert r.status_code == status
    assert r.json()["error"]["code"] == code


def test_support_levels_follow_stored_observations(synced: TestClient) -> None:
    items = {c["iso2"]: c["support"] for c in synced.get("/api/countries").json()["items"]}
    assert items["DE"]["level"] == "partial"
    assert "real GDP 2026-Q3" in items["DE"]["reason"]
    assert "unemployment not ingested" in items["DE"]["reason"]
    assert items["FR"]["level"] == "unavailable"  # inflation alone does not make a target
    assert items["US"]["level"] == "unavailable"


def test_catalog_and_source_health_reflect_the_sync(synced: TestClient) -> None:
    catalog = synced.get("/api/indicators/catalog?country=DE").json()
    gdp = next(
        e for e in catalog["countries"][0]["items"] if e["indicator"]["id"] == "real_gdp_qoq"
    )
    assert gdp["ingestion"]["observations"] == 6
    assert gdp["ingestion"]["latest_period"] == "2026-Q3"
    assert gdp["ingestion"]["source_last_success_at"] is not None
    sources = {s["id"]: s for s in synced.get("/api/sources/status").json()["items"]}
    assert sources["ecb"]["status"] == "ok"
    assert sources["eurostat"]["status"] == "degraded"
    assert sources["eurostat"]["last_success_at"] is not None  # a partial run did fetch data
    assert sources["fred"]["status"] == "never_synced"
