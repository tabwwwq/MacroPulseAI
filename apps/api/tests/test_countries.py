from __future__ import annotations

from fastapi.testclient import TestClient


def test_lists_the_five_initial_countries_in_registry_order(client: TestClient) -> None:
    r = client.get("/api/countries")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 5
    assert [c["iso2"] for c in body["items"]] == ["BE", "DE", "FR", "NL", "US"]


def test_support_is_unavailable_until_observations_exist(client: TestClient) -> None:
    for country in client.get("/api/countries").json()["items"]:
        assert country["support"]["level"] == "unavailable"
        assert country["support"]["target"] == "full"
        assert "No observations" in country["support"]["reason"]


def test_euro_area_policy_rate_is_flagged_as_shared(client: TestClient) -> None:
    items = {c["iso2"]: c for c in client.get("/api/countries").json()["items"]}
    assert items["DE"]["policy_rate_scope"] == "euro_area_shared"
    assert items["US"]["policy_rate_scope"] == "national"


def test_get_country_is_case_insensitive(client: TestClient) -> None:
    r = client.get("/api/countries/nl")
    assert r.status_code == 200
    assert r.json()["name"] == "Netherlands"


def test_unsupported_country_returns_422_error_contract(client: TestClient) -> None:
    r = client.get("/api/countries/XX")
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "unsupported_country"
    assert err["details"]["supported"] == ["BE", "DE", "FR", "NL", "US"]
    assert err["request_id"] == r.headers["X-Request-ID"]


def test_malformed_country_code_is_a_validation_error(client: TestClient) -> None:
    r = client.get("/api/countries/DEU")
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert err["details"]["errors"][0]["loc"] == ["path", "iso2"]


def test_unmigrated_database_yields_actionable_503_not_fake_data(bare_client: TestClient) -> None:
    for path in ["/api/countries", "/api/countries/DE", "/api/sources/status"]:
        r = bare_client.get(path)
        assert r.status_code == 503, path
        err = r.json()["error"]
        assert err["code"] == "database_unavailable"
        assert "macropulse db upgrade" in err["message"]
        assert "sqlite" not in err["message"].lower()  # no connection details leak
