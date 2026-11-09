from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from macropulse_api.main import create_app
from macropulse_api.migrate import upgrade
from macropulse_api.models import IngestionRun
from macropulse_api.services.registry_sync import sync_registry

from .conftest import make_settings


def test_all_sources_start_never_synced(client: TestClient) -> None:
    body = client.get("/api/sources/status").json()
    assert [s["id"] for s in body["items"]] == ["eurostat", "ecb", "fred", "worldbank", "oecd"]
    for s in body["items"]:
        assert s["status"] == "never_synced"
        assert s["last_success_at"] is None
        assert s["last_attempt_at"] is None


def test_api_key_presence_is_reported_but_never_exposed(tmp_path: Path) -> None:
    secret = "abcdef0123456789abcdef0123456789"  # fake test value
    application = create_app(make_settings(tmp_path, fred_api_key=secret))
    upgrade(application.state.engine)
    with application.state.sessionmaker() as session:
        sync_registry(session)
    with TestClient(application) as c:
        r = c.get("/api/sources/status")
    assert secret not in r.text
    by_id = {s["id"]: s for s in r.json()["items"]}
    assert by_id["fred"]["api_key_configured"] is True
    assert by_id["eurostat"]["api_key_configured"] is None


def test_missing_fred_key_is_reported_as_not_configured(client: TestClient) -> None:
    by_id = {s["id"]: s for s in client.get("/api/sources/status").json()["items"]}
    assert by_id["fred"]["requires_api_key"] is True
    assert by_id["fred"]["api_key_configured"] is False


def test_status_is_derived_from_recorded_ingestion_runs(app: FastAPI, client: TestClient) -> None:
    t0 = datetime(2026, 1, 5, 6, 0, tzinfo=UTC)
    with app.state.sessionmaker() as session:
        session.add_all(
            [
                IngestionRun(
                    source_id="eurostat",
                    started_at=t0,
                    finished_at=t0 + timedelta(minutes=2),
                    status="succeeded",
                    rows_upserted=1200,
                ),
                IngestionRun(
                    source_id="eurostat",
                    started_at=t0 + timedelta(days=1),
                    finished_at=t0 + timedelta(days=1, minutes=1),
                    status="failed",
                    rows_upserted=0,
                    error_summary="HTTP 503 from upstream",
                ),
            ]
        )
        session.commit()

    eurostat = next(
        s for s in client.get("/api/sources/status").json()["items"] if s["id"] == "eurostat"
    )
    assert eurostat["status"] == "failed"
    assert eurostat["last_error"] == "HTTP 503 from upstream"
    # Freshness is the last *successful* fetch, not the last attempt.
    assert eurostat["last_success_at"].startswith("2026-01-05T06:02:00")
    assert eurostat["last_attempt_at"].startswith("2026-01-06T06:00:00")
