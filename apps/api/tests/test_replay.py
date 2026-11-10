"""Crisis time machine API: replays are the stored walk-forward estimates, inputs respect the
publication lags, outcomes come strictly after the as-of, and unavailable quarters say why.

Mechanics only (synthetic panel); never model quality.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from macropulse_api.models import ModelPrediction, ModelVersion
from macropulse_api.services import replay as replay_service
from macropulse_api.services import training
from macropulse_economics.periods import period_end, shift
from macropulse_ml.metrics import THRESHOLD
from macropulse_ml.target import quarter_index

from .test_recession import _fake_country, _new_app, _patch

H = 4


@pytest.fixture(scope="module")
def machine(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    application = _new_app(tmp_path_factory.mktemp("replay"))
    with pytest.MonkeyPatch.context() as mp:
        _patch(mp)
        mp.setattr(replay_service, "country_inputs", _fake_country)
        training.train(
            application.state.sessionmaker,
            horizons=(H,),
            seed=11,
            artifacts_root=application.state.settings.models_dir,
            today=date(2026, 11, 9),
        )
        with TestClient(application) as c:
            c.app_state = application  # type: ignore[attr-defined]
            yield c


def _replay(client: TestClient, **params: object) -> dict:  # type: ignore[type-arg]
    r = client.get("/api/history/replay", params={"country": "DE", "horizon": H, **params})
    assert r.status_code == 200, r.text
    body: dict = r.json()  # type: ignore[type-arg]
    return body


def _stored(client: TestClient, country: str, as_of: str) -> ModelPrediction:
    app: FastAPI = client.app_state  # type: ignore[attr-defined]
    with app.state.sessionmaker() as s:
        v = s.scalars(
            select(ModelVersion).where(ModelVersion.selected.is_(True), ModelVersion.horizon == H)
        ).one()
        row = s.scalars(
            select(ModelPrediction).where(
                ModelPrediction.model_version_id == v.id,
                ModelPrediction.country == country,
                ModelPrediction.as_of == as_of,
                ModelPrediction.split != "live",
            )
        ).one()
        s.expunge(row)
        return row


@pytest.mark.parametrize("as_of", ["2008-Q2", "2016-Q3"])
def test_replay_is_the_stored_walk_forward_estimate(machine: TestClient, as_of: str) -> None:
    body = _replay(machine, as_of=as_of)
    stored = _stored(machine, "DE", as_of)
    assert body["probability"] == pytest.approx(stored.probability, abs=1e-12)
    assert body["model"]["fold_year"] == stored.fold_year == int(as_of[:4])
    assert body["model"]["split"] == ("development" if as_of < "2015" else "heldout")
    assert body["model"]["trained_through_as_of"] == shift(f"{as_of[:4]}-Q1", -1 - H)
    assert body["baseline_probability"] is not None
    assert body["basis"]["label"] == "Revised-data / release-lag approximation"
    assert body["basis"]["vintages_available"] is False


def test_inputs_were_published_by_the_cutoff_and_outcomes_come_after(machine: TestClient) -> None:
    body = _replay(machine, as_of="2008-Q2")
    cutoff = date.fromisoformat(body["cutoff"])
    assert cutoff == period_end("2008-Q2")
    assert len(body["inputs"]) == 11
    for i in body["inputs"]:
        assert period_end(i["period"]) + timedelta(days=i["publication_lag_days"]) <= cutoff, i
    for g in body["gdp"]:
        published = period_end(g["period"]) + timedelta(days=60)
        assert (published <= cutoff) is g["known_at_as_of"], g
    window = body["outcome"]["window"]
    assert window == [shift("2008-Q2", k) for k in range(1, H + 1)]
    for e in body["outcome"]["events"]:
        assert quarter_index(e["end"]) >= quarter_index(window[0])
    label, p = body["outcome"]["label"], body["probability"]
    expected = {
        1: "hit" if p >= THRESHOLD else "miss",
        0: "false_alarm" if p >= THRESHOLD else "correct_quiet",
    }
    assert body["outcome"]["verdict"] == expected[label]
    assert body["nber"] is None  # US-only external reference


def test_us_replay_states_the_missing_vintages(machine: TestClient) -> None:
    body = _replay(machine, country="US", as_of="2008-Q2")
    note = body["basis"]["vintage_note"]
    assert "ALFRED" in note
    assert "not configured" in note


def test_quarter_before_the_first_fold_is_unavailable_with_the_reason(machine: TestClient) -> None:
    r = machine.get(
        "/api/history/replay", params={"country": "DE", "horizon": H, "as_of": "1990-Q1"}
    )
    assert r.status_code == 404
    err = r.json()["error"]
    assert err["code"] == "replay_unavailable"
    assert "in-sample" in err["message"]
    assert err["details"]["first"] <= "2001-Q1"


@pytest.mark.parametrize(
    ("params", "status", "code"),
    [
        ({"country": "XX", "as_of": "2008-Q2"}, 422, "unsupported_country"),
        ({"horizon": 3, "as_of": "2008-Q2"}, 422, "unsupported_horizon"),
        ({"as_of": "2099-Q1"}, 422, "invalid_as_of"),
        ({"as_of": "2008Q2"}, 422, "validation_error"),
        ({}, 422, "validation_error"),
        ({"horizon": 2, "as_of": "2008-Q2"}, 503, "model_not_trained"),
    ],
)
def test_replay_rejections(machine: TestClient, params: dict, status: int, code: str) -> None:  # type: ignore[type-arg]
    r = machine.get("/api/history/replay", params={"country": "DE", "horizon": H, **params})
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


def test_episodes_match_the_stored_estimates(machine: TestClient) -> None:
    r = machine.get("/api/history/episodes", params={"country": "DE", "horizon": H})
    assert r.status_code == 200, r.text
    body = r.json()
    app: FastAPI = machine.app_state  # type: ignore[attr-defined]
    with app.state.sessionmaker() as s:
        rows = s.scalars(
            select(ModelPrediction).where(
                ModelPrediction.model_version_id == body["model_id"],
                ModelPrediction.country == "DE",
                ModelPrediction.split.in_(("development", "heldout")),
            )
        ).all()
    assert sum(body["confusion"].values()) == len(rows)
    assert body["confusion"]["tp"] == sum(
        1 for x in rows if x.label == 1 and x.probability >= THRESHOLD
    )
    first = body["first_as_of"]
    for rec in body["recessions"]:
        assert len(rec["warning_as_of"]) == H - 1
        assert all(quarter_index(q) < quarter_index(rec["start"]) for q in rec["warning_as_of"])
        if rec["status"] == "not_evaluable":
            assert all(quarter_index(q) < quarter_index(first) for q in rec["warning_as_of"])
        else:
            assert (rec["status"] == "warned") is (rec["max_probability"] >= THRESHOLD)
    flagged = {x.as_of for x in rows if x.label == 0 and x.probability >= THRESHOLD}
    covered = set()
    for fa in body["false_alarms"]:
        q = fa["start"]
        for _ in range(fa["quarters"]):
            covered.add(q)
            q = shift(q, 1)
    assert covered == flagged


def test_presets_name_real_crisis_quarters(machine: TestClient) -> None:
    body = machine.get("/api/history/presets").json()
    assert [p["as_of"] for p in body] == ["2008-Q2", "2011-Q3", "2019-Q4", "2022-Q2"]
