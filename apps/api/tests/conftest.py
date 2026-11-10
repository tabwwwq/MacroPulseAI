from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from macropulse_api.config import Settings
from macropulse_api.main import create_app
from macropulse_api.migrate import upgrade
from macropulse_api.services.registry_sync import sync_registry


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "test",
        "log_level": "WARNING",
        "database_url": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        "api_cors_origins": ["http://localhost:3000"],
        "fred_api_key": None,
        "models_dir": tmp_path / "artifacts",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    application = create_app(settings)
    upgrade(application.state.engine)
    with application.state.sessionmaker() as session:
        sync_registry(session)
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def bare_client(settings: Settings) -> Iterator[TestClient]:
    """App over an empty, un-migrated database."""
    with TestClient(create_app(settings)) as c:
        yield c
