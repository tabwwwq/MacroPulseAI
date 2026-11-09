from __future__ import annotations

from fastapi.testclient import TestClient

from macropulse_api import __version__


def test_health_is_ok_without_database(bare_client: TestClient) -> None:
    r = bare_client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "macropulse-api"
    assert body["version"] == __version__
    assert body["environment"] == "test"
    assert body["time_utc"].endswith(("Z", "+00:00"))


def test_every_response_carries_a_request_id(client: TestClient) -> None:
    r = client.get("/api/health")
    assert len(r.headers["X-Request-ID"]) >= 8


def test_valid_incoming_request_id_is_propagated(client: TestClient) -> None:
    r = client.get("/api/health", headers={"X-Request-ID": "trace-abc12345"})
    assert r.headers["X-Request-ID"] == "trace-abc12345"


def test_malformed_incoming_request_id_is_replaced(client: TestClient) -> None:
    r = client.get("/api/health", headers={"X-Request-ID": "bad id with spaces"})
    assert r.headers["X-Request-ID"] != "bad id with spaces"


def test_ready_when_migrated_and_seeded(client: TestClient) -> None:
    r = client.get("/api/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert {c["name"] for c in body["checks"]} == {"database", "schema", "registry"}
    assert all(c["ok"] for c in body["checks"])


def test_not_ready_on_unmigrated_database_with_actionable_hint(bare_client: TestClient) -> None:
    r = bare_client.get("/api/ready")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not_ready"
    schema = next(c for c in body["checks"] if c["name"] == "schema")
    assert schema["ok"] is False
    assert "macropulse db upgrade" in schema["detail"]
