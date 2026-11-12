"""US replay on the figures as first published: the re-fitted fold model must reproduce the stored
walk-forward estimate before it scores vintage inputs; nothing published after the cut-off is used.

Mechanics only (synthetic levels turned into ALFRED-style vintages); never model quality.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from macropulse_api.models import ModelPrediction, ModelVersion, VintageSeries
from macropulse_api.models import VintageObservation as VintageRow
from macropulse_api.services import inference, training
from macropulse_api.services import vintage_replay as vr
from macropulse_api.services.vintages import sync_vintages
from macropulse_economics.connectors import SeriesRequest
from macropulse_economics.connectors.alfred import VintageFetch
from macropulse_economics.connectors.alfred import VintageObservation as V
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.periods import period_end
from macropulse_economics.transforms import IDENTITY, Transform
from macropulse_economics.vintages import vintage_series
from macropulse_ml.features import CountryInputs

from .fixture_sources import synthetic_country_inputs
from .test_recession import _new_app

H = 4
AS_OF = "2008-Q3"
KEY = "0123456789abcdef0123456789abcdef"  # fake test value
CURRENT = date(2026, 10, 15)  # start of the latest (benchmark) vintage
RELEASE_DAYS = {"GDPC1": 25, "CPIAUCSL": 12, "UNRATE": 7}


def _levels() -> dict[str, dict[str, float]]:
    """Level series whose derived growth reproduces the synthetic US inputs."""
    base = synthetic_country_inputs("US", 2)
    gdp: dict[str, float] = {}
    level = 100.0
    for period, growth in sorted(base.gdp_qoq.items()):
        level = level * (1 + growth / 100) if gdp else 100.0
        gdp[period] = level
    cpi: dict[str, float] = {}
    months = sorted(base.inflation)
    for i, month in enumerate(months):
        cpi[month] = 100.0 if i < 12 else cpi[months[i - 12]] * (1 + base.inflation[month] / 100)
    return {"GDPC1": gdp, "CPIAUCSL": cpi, "UNRATE": dict(base.unemployment)}


LEVELS = _levels()
First = Callable[[str, str, float], float]


def _rows(first: First, archive_from: dict[str, date] | None = None) -> dict[str, list[V]]:
    """Two vintages per period: the first release (value from `first`) until CURRENT, then the
    current value. Periods first published before `archive_from` appear only from that day on
    (back-filled history, as ALFRED does)."""
    out: dict[str, list[V]] = {}
    for series, levels in LEVELS.items():
        rows: list[V] = []
        for period, value in levels.items():
            published = period_end(period) + timedelta(days=RELEASE_DAYS[series])
            published = max(published, (archive_from or {}).get(series, published))
            if published >= CURRENT:
                rows.append(V(period, value, published, None))
                continue
            rows.append(V(period, first(series, period, value), published, CURRENT - timedelta(1)))
            rows.append(V(period, value, CURRENT, None))
        out[series] = rows
    return out


CURRENT_ROWS = _rows(lambda _s, _p, v: v)
US = replace(
    synthetic_country_inputs("US", 2),
    gdp_qoq=vintage_series(CURRENT_ROWS["GDPC1"], None, Transform("growth", 1)),
    gdp_yoy=vintage_series(CURRENT_ROWS["GDPC1"], None, Transform("growth", 4)),
    inflation=vintage_series(CURRENT_ROWS["CPIAUCSL"], None, Transform("growth", 12)),
    unemployment=vintage_series(CURRENT_ROWS["UNRATE"], None, IDENTITY),
)
INPUTS = {"DE": synthetic_country_inputs("DE", 1), "US": US}


def _fake_load(_session: object) -> tuple[list[CountryInputs], dict[str, str], str]:
    return list(INPUTS.values()), {}, "sha256:test"


def _fake_country(_session: object, iso2: str) -> tuple[CountryInputs, None]:
    return INPUTS[iso2], None


@pytest.fixture(scope="module")
def lab(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[FastAPI, TestClient]]:
    application = _new_app(tmp_path_factory.mktemp("vintage-replay"))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(training, "load_inputs", _fake_load)
        mp.setattr(inference, "country_inputs", _fake_country)
        mp.setattr(vr, "load_inputs", _fake_load)
        mp.setattr(vr, "country_inputs", _fake_country)
        vr._cache.clear()
        training.train(
            application.state.sessionmaker,
            horizons=(H,),
            seed=11,
            artifacts_root=application.state.settings.models_dir,
            today=date(2026, 11, 9),
        )
        with TestClient(application) as c:
            yield application, c
        vr._cache.clear()


def _sync(app: FastAPI, rows: dict[str, list[V]]) -> None:
    def fetch(_f: Fetcher, request: SeriesRequest, key: str | None) -> VintageFetch:
        assert key == KEY
        return VintageFetch(
            request=request,
            observations=rows[request.dataset],
            url=f"https://api.stlouisfed.org/fred/series/observations?series_id={request.dataset}",
            retrieved_at=datetime(2026, 11, 12, 8, 0, tzinfo=UTC),
        )

    report = sync_vintages(app.state.sessionmaker, None, KEY, fetch=fetch)
    assert all(o.ok for o in report.outcomes)


def _get(client: TestClient, **params: object) -> dict:  # type: ignore[type-arg]
    r = client.get(
        "/api/history/vintage-replay",
        params={"country": "US", "horizon": H, "as_of": AS_OF, **params},
    )
    assert r.status_code == 200, r.text
    body: dict = r.json()  # type: ignore[type-arg]
    return body


def test_without_vintages_the_endpoint_says_how_to_sync(lab: tuple[FastAPI, TestClient]) -> None:
    app, client = lab
    with app.state.sessionmaker() as s:
        s.execute(delete(VintageRow))
        s.execute(delete(VintageSeries))
        s.commit()
    r = client.get("/api/history/vintage-replay", params={"country": "US", "as_of": AS_OF})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "vintages_not_synced"
    assert "vintages-sync" in r.json()["error"]["message"]


def test_only_the_us_has_vintages_and_inputs_are_validated(
    lab: tuple[FastAPI, TestClient],
) -> None:
    _, client = lab
    r = client.get("/api/history/vintage-replay", params={"country": "DE", "as_of": AS_OF})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "vintages_not_available"
    bad = [{"as_of": "2008-Q5"}, {"horizon": 3}, {"country": "ZZ"}]
    for params in bad:
        query = {"country": "US", "as_of": AS_OF, **params}
        assert client.get("/api/history/vintage-replay", params=query).status_code == 422
    early = client.get("/api/history/vintage-replay", params={"country": "US", "as_of": "1990-Q1"})
    assert early.status_code == 404  # before the first walk-forward year


def test_rebased_levels_give_the_same_estimate(lab: tuple[FastAPI, TestClient]) -> None:
    """A base-year change scales every level of a vintage: growth, and so the estimate, stay."""
    app, client = lab
    _sync(app, _rows(lambda s, _p, v: v * 0.9 if s != "UNRATE" else v))
    body = _get(client)
    assert body["available"] is True and body["reproduced"] is True
    assert body["vintage_date"] == body["cutoff"] == period_end(AS_OF).isoformat()
    assert body["vintage_probability"] == pytest.approx(body["revised_probability"], abs=1e-9)
    assert all(abs(i["difference"]) < 1e-9 for i in body["inputs"])
    assert {i["feature"] for i in body["inputs"] if i["from_vintage"]} == vr.VINTAGE_FEATURES


def test_first_release_inputs_are_used_and_market_rates_are_untouched(
    lab: tuple[FastAPI, TestClient],
) -> None:
    app, client = lab
    _sync(app, _rows(lambda s, _p, v: v + 0.5 if s == "UNRATE" else v))
    body = _get(client)
    assert body["available"] is True
    by_feature = {i["feature"]: i for i in body["inputs"]}
    assert by_feature["unemp"]["difference"] == pytest.approx(0.5)
    assert by_feature["unemp_chg_6m"]["difference"] == pytest.approx(0.0, abs=1e-9)
    for item in body["inputs"]:
        if not item["from_vintage"]:
            assert item["difference"] == 0.0
        for key in ("revised_period", "vintage_period"):
            if item[key] is not None:  # nothing after the cut-off is ever used
                assert period_end(item[key]) <= period_end(AS_OF)
    assert 0.0 <= body["vintage_probability"] <= 1.0
    assert body["vintage_band"]


def test_quarters_before_the_archive_are_unavailable(lab: tuple[FastAPI, TestClient]) -> None:
    app, client = lab
    _sync(app, _rows(lambda _s, _p, v: v, {"UNRATE": date(2010, 1, 1)}))
    body = _get(client)
    assert body["available"] is False
    assert body["vintage_probability"] is None and body["inputs"] == []
    assert body["archive_start"] == "2010-01-01"
    assert "2010-01-01" in body["reason"]
    assert _get(client, as_of="2012-Q2")["available"] is True


def test_a_stored_estimate_that_no_longer_reproduces_is_not_compared(
    lab: tuple[FastAPI, TestClient],
) -> None:
    app, client = lab
    _sync(app, CURRENT_ROWS)
    with app.state.sessionmaker() as s:
        v = s.scalars(
            select(ModelVersion).where(ModelVersion.selected.is_(True), ModelVersion.horizon == H)
        ).one()
        row = s.scalars(
            select(ModelPrediction).where(
                ModelPrediction.model_version_id == v.id,
                ModelPrediction.country == "US",
                ModelPrediction.as_of == "2009-Q1",
            )
        ).one()
        row.probability = min(1.0, row.probability + 0.05)  # data drifted after training
        s.commit()
    body = _get(client, as_of="2009-Q1")
    assert body["available"] is False
    assert body["vintage_probability"] is None
    assert "Retrain" in body["reason"]
