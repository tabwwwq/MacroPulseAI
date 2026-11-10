"""Inference round trip, explanations, history, curves and every unavailable state.

Training runs on a synthetic panel (CI has no synced official data); it exercises mechanics only.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from macropulse_api.main import create_app
from macropulse_api.migrate import upgrade
from macropulse_api.models import ModelVersion
from macropulse_api.services import inference, training
from macropulse_api.services.registry_sync import sync_registry
from macropulse_ml.features import CountryInputs

from .conftest import make_settings
from .fixture_sources import synthetic_country_inputs

INPUTS = {"DE": synthetic_country_inputs("DE", 1), "US": synthetic_country_inputs("US", 2)}


def _fake_load(_session: object) -> tuple[list[CountryInputs], dict[str, str], str]:
    return list(INPUTS.values()), {}, "sha256:test"


def _fake_country(_session: object, iso2: str) -> tuple[CountryInputs, None]:
    return INPUTS[iso2], None


def _patch(mp: pytest.MonkeyPatch) -> None:
    mp.setattr(training, "load_inputs", _fake_load)
    mp.setattr(inference, "country_inputs", _fake_country)


def _new_app(root: Path) -> FastAPI:
    application = create_app(make_settings(root))
    upgrade(application.state.engine)
    with application.state.sessionmaker() as session:
        sync_registry(session)
    return application


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    """One training run (both horizons) shared by the read-only tests of this module."""
    application = _new_app(tmp_path_factory.mktemp("recession"))
    with pytest.MonkeyPatch.context() as mp:
        _patch(mp)
        training.train(
            application.state.sessionmaker,
            horizons=(2, 4),
            seed=11,
            artifacts_root=application.state.settings.models_dir,
            today=date(2026, 11, 9),
        )
        with TestClient(application) as c:
            c.app_state = application  # type: ignore[attr-defined]
            yield c


def _predict(client: TestClient, **params: object) -> dict:  # type: ignore[type-arg]
    r = client.get("/api/recession/predict", params={"country": "DE", "horizon": 4, **params})
    assert r.status_code == 200, r.text
    body: dict = r.json()  # type: ignore[type-arg]
    return body


def test_no_model_is_an_actionable_503(client: TestClient) -> None:
    r = client.get("/api/recession/predict", params={"country": "DE", "horizon": 2})
    assert r.status_code == 503
    err = r.json()["error"]
    assert err["code"] == "model_not_trained"
    assert "macropulse train" in err["message"]


def test_round_trip_matches_the_estimate_stored_at_training(trained: TestClient) -> None:
    for horizon in (2, 4):
        body = _predict(trained, horizon=horizon)
        assert body["as_of"] == "2026-Q3"
        assert 0 <= body["probability"] <= 1
        assert body["stored_estimate"] == pytest.approx(body["probability"], abs=1e-12)
        assert body["model"]["id"].endswith(f"-h{horizon}-" + body["model"]["key"])
        assert body["band"] in {b["name"] for b in body["bands"]}
        assert body["outcome"]["status"] == "censored"
        assert body["in_sample"] is False
        assert len(body["explanation"]["items"]) == 11
        assert "development" in body["track_record"]
        assert body["event_definition"].startswith("Technical recession within the next")
        assert body["limitations"]


def test_logistic_explanation_adds_up_to_the_log_odds(trained: TestClient) -> None:
    app: FastAPI = trained.app_state  # type: ignore[attr-defined]
    with app.state.sessionmaker() as s:
        published = {
            v.horizon: v.model_key
            for v in s.query(ModelVersion).filter(ModelVersion.selected.is_(True)).all()
        }
    for horizon, key in published.items():
        body = _predict(trained, horizon=horizon)
        expl = body["explanation"]
        if key == "logistic":
            total = expl["intercept"] + sum(i["contribution"] for i in expl["items"])
            p = body["probability"]
            assert total == pytest.approx(math.log(p / (1 - p)), abs=1e-6)
            assert expl["unit"] == "log-odds"
        else:
            assert expl["unit"] in {"probability", "log-odds"}
        contributions = [abs(i["contribution"]) for i in expl["items"]]
        assert contributions == sorted(contributions, reverse=True)


def test_historical_as_of_is_flagged_in_sample_with_the_walk_forward_estimate(
    trained: TestClient,
) -> None:
    body = _predict(trained, as_of="2010-Q2")
    assert body["in_sample"] is True
    assert body["walk_forward_probability"] is not None
    assert body["walk_forward_split"] == "development"
    assert body["outcome"]["status"] == "observed"
    assert body["outcome"]["label"] in (0, 1)


@pytest.mark.parametrize(
    ("params", "status", "code"),
    [
        ({"country": "XX", "horizon": 2}, 422, "unsupported_country"),
        ({"country": "DE", "horizon": 3}, 422, "unsupported_horizon"),
        ({"country": "DE", "horizon": 2, "as_of": "2099-Q1"}, 422, "invalid_as_of"),
        ({"country": "DE", "horizon": 2, "as_of": "2026Q1"}, 422, "validation_error"),
        ({"country": "DE", "horizon": 2, "as_of": "1960-Q1"}, 404, "features_unavailable"),
    ],
)
def test_invalid_requests(trained: TestClient, params: dict, status: int, code: str) -> None:  # type: ignore[type-arg]
    r = trained.get("/api/recession/predict", params=params)
    assert r.status_code == status
    assert r.json()["error"]["code"] == code


def test_missing_and_untrusted_artifacts_are_refused(
    app: FastAPI, client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch(monkeypatch)
    training.train(
        app.state.sessionmaker,
        horizons=(4,),
        seed=11,
        artifacts_root=app.state.settings.models_dir,
        today=date(2026, 11, 9),
    )
    with app.state.sessionmaker() as s:
        v = s.query(ModelVersion).filter(ModelVersion.selected.is_(True)).one()
        artifact = Path(v.artifact_path or "") / "model.joblib"
        outside = tmp_path / "elsewhere"
        outside.mkdir()
        (outside / "model.joblib").write_bytes(artifact.read_bytes())
        v.artifact_path = str(outside)
        s.commit()
    r = client.get("/api/recession/predict", params={"country": "DE", "horizon": 4})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "model_artifact_untrusted"

    with app.state.sessionmaker() as s:
        v = s.query(ModelVersion).filter(ModelVersion.selected.is_(True)).one()
        v.artifact_path = str(artifact.parent)
        s.commit()
    artifact.unlink()
    r = client.get("/api/recession/predict", params={"country": "DE", "horizon": 4})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "model_artifact_missing"


def test_history_is_out_of_sample_with_baseline_and_events(trained: TestClient) -> None:
    r = trained.get("/api/recession/history", params={"country": "US", "horizon": 2})
    assert r.status_code == 200
    body = r.json()
    splits = {p["split"] for p in body["points"]}
    assert {"development", "heldout", "live"} <= splits
    assert body["points"][-1]["split"] == "live"
    assert all(p["fold_year"] is not None for p in body["points"] if p["split"] != "live")
    assert body["baseline"] and all(p["split"] != "live" for p in body["baseline"])
    assert "walk-forward" in body["note"]


def test_curves_are_computed_from_stored_predictions(trained: TestClient) -> None:
    models = trained.get("/api/models").json()["items"]
    selected = next(m for m in models if m["selected"])
    body = trained.get(f"/api/models/{selected['id']}/curves").json()
    assert [s["split"] for s in body["splits"]] == ["development", "heldout"]
    for s in body["splits"]:
        if s["roc"] is None:
            assert s["note"]
            continue
        assert s["roc"][0] == {"x": 0.0, "y": 0.0}
        assert s["roc"][-1] == {"x": 1.0, "y": 1.0}
        assert all(0 <= p["y"] <= 1 for p in s["pr"])
