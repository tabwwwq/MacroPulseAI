"""PostgreSQL compatibility: same migrations and endpoints on the production database engine.

Skipped unless MACROPULSE_TEST_POSTGRES_URL is set (CI provides a postgres service container).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from macropulse_api.main import create_app
from macropulse_api.migrate import current_revision, downgrade, head_revision, upgrade
from macropulse_api.services.registry_sync import sync_registry

from .conftest import make_settings

PG_URL = os.environ.get("MACROPULSE_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(not PG_URL, reason="MACROPULSE_TEST_POSTGRES_URL not set")


def test_migrations_and_endpoints_on_postgres(tmp_path: Path) -> None:
    app = create_app(make_settings(tmp_path, database_url=PG_URL))
    engine = app.state.engine
    downgrade(engine, "base")  # start from a clean schema
    upgrade(engine)
    assert current_revision(engine) == head_revision()
    with app.state.sessionmaker() as session:
        sync_registry(session)
        sync_registry(session)  # idempotent

    with TestClient(app) as client:
        ready = client.get("/api/ready")
        assert ready.status_code == 200, ready.json()
        assert ready.json()["checks"][0]["detail"] == "postgresql"
        assert client.get("/api/countries").json()["count"] == 5
        assert client.get("/api/countries/US").json()["policy_rate_scope"] == "national"
        assert len(client.get("/api/sources/status").json()["items"]) == 5

    downgrade(engine, "base")
    engine.dispose()
