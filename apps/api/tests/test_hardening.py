"""Release hardening: body limits, security headers, credential redaction in provenance."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from macropulse_api.middleware import MAX_BODY_BYTES
from macropulse_api.models import IngestionRun, Observation, QualityCheck
from macropulse_economics.connectors import FetchResult, SeriesRequest
from macropulse_economics.connectors.http import Fetcher

from .fixture_sources import fixture_fetch, offline_fetcher, sync_fixtures

SECRET = "0123456789abcdef" * 2


def test_oversized_and_unsized_bodies_are_refused(client: TestClient) -> None:
    big = {"country": "DE", "horizon": 4, "pad": "x" * (MAX_BODY_BYTES + 10)}
    r = client.post("/api/scenarios/evaluate", json=big)
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
    assert r.json()["error"]["request_id"] == r.headers["X-Request-ID"]

    def chunks() -> Iterator[bytes]:
        yield b'{"country": "DE", "format": "json"}'

    r = client.post(
        "/api/reports/generate", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 411
    assert r.json()["error"]["code"] == "length_required"


def test_every_response_carries_security_headers(client: TestClient) -> None:
    for path in ("/api/health", "/api/countries", "/api/does-not-exist"):
        r = client.get(path)
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Referrer-Policy"] == "no-referrer"


def test_credentials_in_source_urls_never_reach_storage_or_api(
    app: FastAPI, client: TestClient
) -> None:
    def leaky_fetch(fetcher: Fetcher, req: SeriesRequest) -> FetchResult:
        result = fixture_fetch(fetcher, req)
        result.url = f"{result.url}&api_key={SECRET}"
        return result

    sync_fixtures(app, offline_fetcher(), fetch=leaky_fetch)
    with app.state.sessionmaker() as s:
        urls = [o.source_url for o in s.scalars(select(Observation))]
        texts = [c.detail for c in s.scalars(select(QualityCheck))]
        texts += [r.error_summary or "" for r in s.scalars(select(IngestionRun))]
    assert urls and all(SECRET not in u and "api_key=REDACTED" in u for u in urls)
    assert all(SECRET not in t for t in texts)
    body = client.get("/api/indicators", params={"country": "DE", "indicator": "real_gdp_qoq"})
    assert SECRET not in body.text
    assert "api_key=REDACTED" in body.json()["provenance"]["request_url"]
