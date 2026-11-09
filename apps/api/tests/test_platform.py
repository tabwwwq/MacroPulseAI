"""Cross-cutting behaviour: error contract, CORS, OpenAPI, migrations."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from macropulse_api.migrate import current_revision, downgrade, head_revision, upgrade


def test_unknown_route_uses_error_contract(client: TestClient) -> None:
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_wrong_method_uses_error_contract(client: TestClient) -> None:
    r = client.post("/api/health")
    assert r.status_code == 405
    assert r.json()["error"]["code"] == "method_not_allowed"


def test_cors_allows_configured_origin_only(client: TestClient) -> None:
    ok = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_openapi_documents_the_public_endpoints(client: TestClient) -> None:
    paths = client.get("/api/openapi.json").json()["paths"]
    for p in [
        "/api/health",
        "/api/ready",
        "/api/countries",
        "/api/countries/{iso2}",
        "/api/sources/status",
    ]:
        assert p in paths


def test_migrations_round_trip(app: FastAPI) -> None:
    engine = app.state.engine
    assert current_revision(engine) == head_revision()
    downgrade(engine, "base")
    assert current_revision(engine) is None
    assert "countries" not in inspect(engine).get_table_names()
    upgrade(engine)
    assert {"countries", "data_sources", "ingestion_runs"} <= set(inspect(engine).get_table_names())
