from __future__ import annotations

from fastapi.testclient import TestClient


def _entry(body: dict, iso: str, indicator: str) -> dict:
    country = next(c for c in body["countries"] if c["country"] == iso)
    return next(e for e in country["items"] if e["indicator"]["id"] == indicator)


def test_catalog_covers_all_countries_and_indicators(client: TestClient) -> None:
    body = client.get("/api/indicators/catalog").json()
    assert body["probe_date"] == "2026-11-08"
    assert [c["country"] for c in body["countries"]] == ["BE", "DE", "FR", "NL", "US"]
    assert all(len(c["items"]) == 9 for c in body["countries"])


def test_single_country_filter_is_case_insensitive(client: TestClient) -> None:
    body = client.get("/api/indicators/catalog?country=de").json()
    assert [c["country"] for c in body["countries"]] == ["DE"]


def test_mapping_reflects_probe_findings_and_no_observations(client: TestClient) -> None:
    body = client.get("/api/indicators/catalog").json()
    gdp = _entry(body, "DE", "real_gdp_qoq")
    assert gdp["mapping"]["status"] == "verified"
    assert gdp["mapping"]["dataset"] == "namq_10_gdp"
    assert gdp["mapping"]["source_name"] == "Eurostat dissemination API"
    assert gdp["ingestion"] == {
        "observations": 0,
        "latest_period": None,
        "source_last_success_at": None,
    }
    assert _entry(body, "FR", "inflation_yoy")["mapping"]["dataset"] == "prc_hicp_minr"
    assert _entry(body, "NL", "cli")["mapping"]["status"] == "not_published"
    assert _entry(body, "DE", "yield_spread")["mapping"]["status"] == "unmapped"
    assert _entry(body, "US", "nber_recession")["indicator"]["category"] == "reference"


def test_catalog_rejects_unsupported_and_malformed_countries(client: TestClient) -> None:
    unsupported = client.get("/api/indicators/catalog?country=XX")
    assert unsupported.status_code == 422
    assert unsupported.json()["error"]["code"] == "unsupported_country"
    malformed = client.get("/api/indicators/catalog?country=DEU")
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "validation_error"
