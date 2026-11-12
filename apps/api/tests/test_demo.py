"""Demo snapshot: export -> load reproduces the stored rows, is marked as snapshot data and keeps
the original retrieval time as freshness."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from macropulse_api.models import IngestionRun, Observation
from macropulse_api.services.demo import (
    DEFAULT_SNAPSHOT,
    NOT_IN_SNAPSHOT,
    export_snapshot,
    load_snapshot,
    read_snapshot,
)

from .fixture_sources import offline_fetcher, sync_fixtures
from .test_recession import _new_app


def _rows(app: FastAPI) -> list[tuple[str, str, float, str | None, str, str]]:
    with app.state.sessionmaker() as s:
        return [
            (o.series_id, o.period, o.value, o.obs_status, o.source_url, str(o.retrieved_at)[:19])
            for o in s.scalars(
                select(Observation).order_by(Observation.series_id, Observation.period)
            )
        ]


def test_snapshot_round_trip_is_exact_and_labelled(app: FastAPI, tmp_path: Path) -> None:
    sync_fixtures(app, offline_fetcher())
    path = tmp_path / "snap.json.gz"
    with app.state.sessionmaker() as s:
        header = export_snapshot(s, path)
    assert header["observation_count"] == len(_rows(app)) > 0

    demo = _new_app(tmp_path / "demo")
    report, captured = load_snapshot(demo.state.sessionmaker, path)
    assert _rows(demo) == _rows(app)
    assert captured == datetime.fromisoformat(header["captured_at"])
    with demo.state.sessionmaker() as s:
        runs = s.scalars(select(IngestionRun)).all()
    assert runs and all(r.mode == "snapshot" for r in runs)
    # Series the registry knows but the snapshot lacks are reported, never invented.
    missing = [o for o in report.outcomes if not o.ok]
    assert all("not in the demo snapshot" in (o.error or "") for o in missing)

    with TestClient(demo) as client:
        items = client.get("/api/sources/status").json()["items"]
    loaded = [i for i in items if i["data_mode"] == "snapshot"]
    assert loaded
    for item in loaded:
        assert item["snapshot_taken_at"].startswith(header["captured_at"][:19])
        assert item["last_success_at"] == item["snapshot_taken_at"]  # freshness = capture time


def test_live_sync_is_labelled_live(app: FastAPI, client: TestClient) -> None:
    sync_fixtures(app, offline_fetcher())
    items = client.get("/api/sources/status").json()["items"]
    synced = [i for i in items if i["last_success_at"]]
    assert synced and all(
        i["data_mode"] == "live" and i["snapshot_taken_at"] is None for i in synced
    )
    assert all(i["data_mode"] is None for i in items if not i["last_success_at"])


def test_series_registered_after_the_snapshot_are_not_failures(tmp_path: Path) -> None:
    """The bundled snapshot predates the OECD connector: its series must stay "never synced",
    not turn the demo load into a failure (CI 43264272331)."""
    app = _new_app(tmp_path)
    report, _ = load_snapshot(app.state.sessionmaker)
    assert [o.series_id for o in report.outcomes if not o.ok] == []
    later = [s for s in report.skipped if s.endswith(NOT_IN_SNAPSHOT)]
    assert len(later) == 13 and all(s.startswith("oecd:") for s in later)
    with app.state.sessionmaker() as s:
        runs = s.scalars(select(IngestionRun)).all()
        assert {r.source_id for r in runs} == {"eurostat", "ecb", "fred"}
        assert {r.status for r in runs} == {"succeeded"}


def test_bundled_snapshot_is_genuine_and_complete() -> None:
    data = read_snapshot(DEFAULT_SNAPSHOT)
    assert data["captured_at"].startswith("2026-11-09")
    assert data["series_count"] == len(data["series"]) == 31
    assert data["observation_count"] == sum(len(s["observations"]) for s in data["series"])
    for s in data["series"]:
        assert s["url"].startswith("https://"), s["series_id"]
        assert s["retrieved_at"].startswith("2026-11-09"), s["series_id"]
        assert "api_key" not in s["url"]
