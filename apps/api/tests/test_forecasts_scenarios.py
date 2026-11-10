"""Forecast studio and scenario lab endpoints.

Forecasts run over the real DE GDP fixture extended backwards with synthetic quarters (the
fixture alone is too short to backtest). Scenarios use a model trained on a synthetic panel.
Both exercise mechanics only and never stand for forecast or model quality.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from macropulse_api.main import create_app
from macropulse_api.migrate import upgrade
from macropulse_api.models import Observation
from macropulse_api.ratelimit import RateLimiter
from macropulse_api.services import scenarios, training
from macropulse_api.services.registry_sync import sync_registry
from macropulse_economics.periods import period_start, shift
from macropulse_ml.features import FEATURE_NAMES

from .conftest import make_settings
from .fixture_sources import DE_GDP_ID, offline_fetcher, sync_fixtures
from .test_recession import _fake_country, _new_app, _patch

# --- forecasts --------------------------------------------------------------------------------


def _extend_de_gdp(app: FastAPI, first: str = "1995-Q1") -> None:
    """Prepend synthetic quarterly levels so the stored DE GDP series is long enough."""
    with app.state.sessionmaker() as s:
        rows = s.scalars(
            select(Observation)
            .where(Observation.series_id == DE_GDP_ID)
            .order_by(Observation.period_start)
        ).all()
        oldest = rows[0]
        periods = []
        p = first
        while p != oldest.period:
            periods.append(p)
            p = shift(p, 1)
        rng = np.random.default_rng(4)
        level = oldest.value
        for period in reversed(periods):
            level /= 1 + (0.4 + 0.5 * rng.standard_normal()) / 100
            s.add(
                Observation(
                    series_id=oldest.series_id,
                    source_id=oldest.source_id,
                    geo=oldest.geo,
                    dataset=oldest.dataset,
                    series_key=oldest.series_key,
                    period=period,
                    period_start=period_start(period),
                    frequency=oldest.frequency,
                    value=level,
                    unit=oldest.unit,
                    adjustment=oldest.adjustment,
                    obs_status=None,
                    source_url=oldest.source_url,
                    source_updated_at=oldest.source_updated_at,
                    retrieved_at=oldest.retrieved_at,
                    ingestion_run_id=oldest.ingestion_run_id,
                )
            )
        s.commit()


@pytest.fixture
def long_gdp(app: FastAPI, client: TestClient) -> TestClient:
    sync_fixtures(app, offline_fetcher())
    _extend_de_gdp(app)
    return client


def _forecast(client: TestClient, **params: object) -> dict:  # type: ignore[type-arg]
    q = {"country": "DE", "metric": "real_gdp_qoq", "horizon": 4, **params}
    r = client.get("/api/forecasts", params=q)
    assert r.status_code == 200, r.text
    body: dict = r.json()  # type: ignore[type-arg]
    return body


def test_latest_forecast_starts_after_the_last_published_quarter(long_gdp: TestClient) -> None:
    body = _forecast(long_gdp)
    assert body["origin"] == "2026-Q3"
    assert body["actuals"][-1]["period"] == "2026-Q3"
    assert body["realised"] == []
    assert body["steps"] == 4
    assert {m["key"] for m in body["models"]} == {"naive", "mean", "ar"}
    for m in body["models"]:
        assert [p["period"] for p in m["path"]] == ["2026-Q4", "2027-Q1", "2027-Q2", "2027-Q3"]
        for p in m["path"]:
            if p["lower"] is not None:
                assert p["lower"] <= p["value"] <= p["upper"]
                assert p["n_errors"] >= body["min_errors"]
    naive = next(m for m in body["models"] if m["key"] == "naive")
    assert all(p["value"] == pytest.approx(body["actuals"][-1]["value"]) for p in naive["path"])
    steps = {(m["model"], m["step"]) for m in body["backtest"]["metrics"]}
    assert {("ar", s) for s in (1, 2, 4, 8)} <= steps
    assert {e["model"] for e in body["errors"]} == {"naive", "mean", "ar"}
    assert all(e["target"] <= body["origin"] for e in body["errors"])
    assert body["provenance"]["series_id"] == DE_GDP_ID
    assert body["nominal_coverage"] == 0.8
    assert body["assumptions"]


def test_past_as_of_uses_only_what_was_published_and_returns_the_realised_path(
    long_gdp: TestClient,
) -> None:
    body = _forecast(long_gdp, as_of="2010-Q2")
    # Q1 ends 31 March; with the 60-day GDP lag it is out by 30 June, Q2 is not.
    assert body["origin"] == "2010-Q1"
    assert body["actuals"][-1]["period"] == "2010-Q1"
    assert [r["period"] for r in body["realised"]] == ["2010-Q2", "2010-Q3", "2010-Q4", "2011-Q1"]
    assert body["backtest"]["last_origin"] < "2010-Q1"
    latest = _forecast(long_gdp)
    same = {a["period"]: a["value"] for a in latest["actuals"]}
    assert all(a["value"] == pytest.approx(same[a["period"]]) for a in body["actuals"])


def test_monthly_horizon_is_counted_in_months(long_gdp: TestClient) -> None:
    r = long_gdp.get(
        "/api/forecasts", params={"country": "FR", "metric": "inflation_yoy", "horizon": 2}
    )
    # The FR HICP fixture holds four months only: honest 404, not a made-up forecast.
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "forecast_unavailable"


@pytest.mark.parametrize(
    ("params", "status", "code"),
    [
        ({"metric": "gdp_level"}, 422, "unsupported_metric"),
        ({"horizon": 3}, 422, "unsupported_horizon"),
        ({"as_of": "2099-Q1"}, 422, "invalid_as_of"),
        ({"as_of": "2010Q1"}, 422, "validation_error"),
        ({"country": "XX"}, 422, "unsupported_country"),
        ({"country": "US"}, 503, "data_not_synced"),
        ({"as_of": "1996-Q1"}, 404, "forecast_unavailable"),
    ],
)
def test_forecast_rejections(
    long_gdp: TestClient,
    params: dict,  # type: ignore[type-arg]
    status: int,
    code: str,
) -> None:
    q = {"country": "DE", "metric": "real_gdp_qoq", "horizon": 4, **params}
    r = long_gdp.get("/api/forecasts", params=q)
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


# --- scenarios --------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def lab(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    """A published H=4 model only (H=2 deliberately untrained)."""
    application = _new_app(tmp_path_factory.mktemp("scenarios"))
    with pytest.MonkeyPatch.context() as mp:
        _patch(mp)
        mp.setattr(scenarios, "country_inputs", _fake_country)
        training.train(
            application.state.sessionmaker,
            horizons=(4,),
            seed=11,
            artifacts_root=application.state.settings.models_dir,
            today=date(2026, 11, 9),
        )
        with TestClient(application) as c:
            yield c


def _evaluate(client: TestClient, **body: object) -> dict:  # type: ignore[type-arg]
    r = client.post("/api/scenarios/evaluate", json={"country": "DE", "horizon": 4, **body})
    assert r.status_code == 200, r.text
    out: dict = r.json()  # type: ignore[type-arg]
    return out


def test_spec_lists_bounded_shocks_and_the_disclaimer(lab: TestClient) -> None:
    body = lab.get("/api/scenarios/spec").json()
    assert body["disclaimer"] == scenarios.DISCLAIMER
    keys = [s["key"] for s in body["shocks"]]
    assert keys == ["gdp", "inflation", "unemployment", "policy_rate", "long_rate"]
    for s in body["shocks"]:
        assert s["minimum"] < 0 < s["maximum"]
        assert s["effect"]


def test_no_shock_reproduces_the_published_estimate(lab: TestClient) -> None:
    body = _evaluate(lab)
    assert body["delta"] == 0
    assert body["scenario"] == body["baseline"]
    assert not any(i["changed"] for i in body["inputs"])
    assert body["disclaimer"] == (
        "Exploratory model sensitivity analysis, not a causal economic simulation."
    )
    estimate = lab.get("/api/recession/predict", params={"country": "DE", "horizon": 4}).json()
    assert body["as_of"] == estimate["as_of"]
    assert body["baseline"]["probability"] == pytest.approx(estimate["probability"], abs=1e-12)
    assert body["joint_check"]["available"] is True


def test_policy_rate_shock_moves_exactly_its_mapped_inputs(lab: TestClient) -> None:
    body = _evaluate(lab, shocks={"policy_rate": 2.0})
    changed = {i["feature"]: i["scenario"] - i["baseline"] for i in body["inputs"] if i["changed"]}
    assert changed == pytest.approx({"rate": 2.0, "rate_chg_4q": 2.0, "term_spread": -2.0})
    assert body["shocks"]["policy_rate"] == 2.0
    assert body["delta"] == pytest.approx(
        body["scenario"]["probability"] - body["baseline"]["probability"]
    )
    deltas = [abs(c["delta"]) for c in body["contributions"]]
    assert deltas == sorted(deltas, reverse=True)
    if body["explanation_unit"] == "log-odds":  # exact additive terms: only shocked inputs move
        moved = {c["feature"] for c in body["contributions"] if c["delta"] != 0}
        assert moved <= set(changed)


def test_extreme_shocks_are_flagged_as_extrapolation(lab: TestClient) -> None:
    extreme = {"gdp": -5, "inflation": 5, "unemployment": 4, "policy_rate": 4, "long_rate": -3}
    body = _evaluate(lab, shocks=extreme)
    assert any(i["outside_training_range"] for i in body["inputs"])
    assert body["joint_check"]["unusual_combination"] is True
    text = " ".join(body["warnings"])
    assert "extrapolating" in text
    assert "Unusual combination" in text


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"shocks": {"gdp": 9}}, 422, "validation_error"),
        ({"shocks": {"oil": 1}}, 422, "validation_error"),
        ({"horizon": 3}, 422, "unsupported_horizon"),
        ({"country": "XX"}, 422, "unsupported_country"),
        ({"as_of": "2099-Q1"}, 422, "invalid_as_of"),
        ({"as_of": "1970-Q1"}, 404, "features_unavailable"),
        ({"horizon": 2}, 503, "model_not_trained"),
    ],
)
def test_scenario_rejections(lab: TestClient, body: dict, status: int, code: str) -> None:  # type: ignore[type-arg]
    r = lab.post("/api/scenarios/evaluate", json={"country": "DE", "horizon": 4, **body})
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


def test_gdp_shock_recounts_negative_quarters() -> None:
    base = dict.fromkeys(FEATURE_NAMES, 0.0) | {"gdp_qoq_1": 0.3, "gdp_neg_4": 1.0}
    down = scenarios.apply_shocks(base, {"gdp": -0.5})
    assert down["gdp_qoq_1"] == pytest.approx(-0.2)
    assert down["gdp_neg_4"] == 2.0
    back = scenarios.apply_shocks(down, {"gdp": 0.5})
    assert back["gdp_neg_4"] == 1.0
    assert base["gdp_qoq_1"] == 0.3  # inputs are not mutated


def test_joint_check_needs_the_training_covariance() -> None:
    x = np.zeros(len(FEATURE_NAMES))
    assert scenarios.joint_check(x, x, {}, None) == {"available": False}
    summary = {n: {"mean": 0.0} for n in FEATURE_NAMES}
    out = scenarios.joint_check(x, x + 10, summary, np.eye(len(FEATURE_NAMES)).tolist())
    assert out["baseline_distance"] == 0
    assert out["scenario_distance"] == pytest.approx(100 * len(FEATURE_NAMES))
    assert out["unusual_combination"] is True


# --- rate limiting ----------------------------------------------------------------------------


def test_rate_limiter_slides_its_window() -> None:
    now = [0.0]
    limiter = RateLimiter(2, clock=lambda: now[0])
    assert limiter.hit("a") is None
    assert limiter.hit("a") is None
    assert limiter.hit("a") == pytest.approx(60.0)
    assert limiter.hit("b") is None  # per client
    now[0] = 30.0
    assert limiter.hit("a") == pytest.approx(30.0)
    now[0] = 60.0
    assert limiter.hit("a") is None
    assert RateLimiter(0).hit("a") is None  # 0 disables


def test_compute_endpoints_answer_429_with_retry_after(tmp_path: Path) -> None:
    application = create_app(make_settings(tmp_path, compute_requests_per_minute=2))
    upgrade(application.state.engine)
    with application.state.sessionmaker() as s:
        sync_registry(s)
    with TestClient(application) as c:
        q = {"country": "DE", "metric": "real_gdp_qoq"}
        assert c.get("/api/forecasts", params=q).status_code == 503  # counted, not limited
        assert (
            c.post("/api/scenarios/evaluate", json={"country": "DE", "horizon": 4}).status_code
            == 503
        )
        r = c.get("/api/forecasts", params=q)
        assert r.status_code == 429
        assert r.json()["error"]["code"] == "rate_limited"
        assert int(r.headers["Retry-After"]) >= 1
        assert c.get("/api/scenarios/spec").status_code == 200  # static spec is not limited
