"""Report builder API over real fixtures: numbers match the API, gaps and untrained models are
labelled, the download is named and failures do not leak internals."""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Iterator
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfReader

from macropulse_api.routers import reports as reports_router
from macropulse_api.services import training
from macropulse_economics.periods import period_end

from .fixture_sources import offline_fetcher, sync_fixtures
from .test_recession import _new_app, _patch


@pytest.fixture
def synced(app: FastAPI, client: TestClient) -> TestClient:
    sync_fixtures(app, offline_fetcher())
    return client


def _report(client: TestClient, fmt: str, **body: object) -> tuple[bytes, dict[str, str]]:
    r = client.post("/api/reports/generate", json={"country": "DE", "format": fmt, **body})
    assert r.status_code == 200, r.text
    return r.content, dict(r.headers)


def test_json_report_matches_the_summary_and_labels_what_is_missing(synced: TestClient) -> None:
    raw, headers = _report(synced, "json")
    assert headers["content-type"].startswith("application/json")
    assert re.fullmatch(
        r'attachment; filename="macropulse-report-de-latest-\d{8}\.json"',
        headers["content-disposition"],
    )
    body = json.loads(raw)
    summary = synced.get("/api/countries/DE/summary").json()
    expected = {k["indicator"]["name"]: k for k in summary["kpis"]}
    for row in body["kpis"]:
        k = expected[row["label"]]
        assert row["value"] == k["value"]
        assert row["period"] == k["period"]
        if k["value"] is None:
            assert row["note"]  # missing values carry the reason
    gdp = next(r for r in body["kpis"] if r["label"] == "Real GDP growth (q/q)")
    assert gdp["citation"]["label"].startswith("Eurostat")
    assert any("Real GDP growth (q/q):" in s for s in body["summary"])
    assert all(r["probability"] is None and "train" in r["note"] for r in body["estimates"])
    assert "No recession probability is shown" in " ".join(body["summary"])
    assert all(f["value"] is None and f["note"] for f in body["forecasts"])
    assert any("chart not included" in w for w in body["warnings"])
    assert body["as_of"] is None
    assert body["disclaimer"].startswith("MacroPulse AI report")


def test_as_of_report_only_uses_periods_up_to_the_cutoff(synced: TestClient) -> None:
    raw, headers = _report(synced, "json", as_of="2026-Q1")
    assert "macropulse-report-de-2026-Q1-" in headers["content-disposition"]
    body = json.loads(raw)
    assert body["as_of_label"] == "As of 2026-Q1 (cut-off 2026-03-31)"
    cutoff = date(2026, 3, 31)
    for row in body["kpis"]:
        if row["period"]:
            assert period_end(row["period"]) <= cutoff, row
    assert body["charts"]
    for chart in body["charts"]:
        for series in chart["series"]:
            assert all(period_end(p) <= cutoff for p, _ in series["points"])


def test_pdf_and_csv_downloads(synced: TestClient) -> None:
    pdf, headers = _report(synced, "pdf")
    assert headers["content-type"] == "application/pdf"
    assert headers["content-disposition"].endswith('.pdf"')
    text = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf)).pages)
    flat = re.sub(r"\s+", " ", text)
    assert "MacroPulse country report: Germany" in flat
    assert "N/A" in flat
    assert "macropulse train" in flat

    raw, headers = _report(synced, "csv")
    assert headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
    assert rows[0][:5] == ["chart", "series", "unit", "period", "value"]
    assert any(r[0] == "Real GDP growth (q/q)" for r in rows[1:])


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"country": "XX"}, 422, "unsupported_country"),
        ({"country": "DE", "as_of": "2099-Q1"}, 422, "invalid_as_of"),
        ({"country": "DE", "format": "docx"}, 422, "validation_error"),
        ({"country": "DE", "extra": 1}, 422, "validation_error"),
    ],
)
def test_report_rejections(synced: TestClient, body: dict, status: int, code: str) -> None:  # type: ignore[type-arg]
    r = synced.post("/api/reports/generate", json=body)
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


def test_rendering_failure_is_a_safe_500(
    synced: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(_content: object, _fmt: str) -> bytes:
        raise RuntimeError(r"C:\secret\path FRED_API_KEY=abc")

    monkeypatch.setattr(reports_router, "_render", boom)
    r = synced.post("/api/reports/generate", json={"country": "DE", "format": "pdf"})
    assert r.status_code == 500
    err = r.json()["error"]
    assert err["code"] == "report_generation_failed"
    assert "secret" not in r.text
    assert "FRED_API_KEY" not in r.text
    assert err["request_id"]


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    application = _new_app(tmp_path_factory.mktemp("reports"))
    sync_fixtures(application, offline_fetcher())
    with pytest.MonkeyPatch.context() as mp:
        _patch(mp)
        training.train(
            application.state.sessionmaker,
            horizons=(4,),
            seed=11,
            artifacts_root=application.state.settings.models_dir,
            today=date(2026, 11, 9),
        )
        with TestClient(application) as c:
            yield c


def test_estimates_come_from_live_inference(trained: TestClient) -> None:
    raw, _ = _report(trained, "json")
    body = json.loads(raw)
    live = trained.get("/api/recession/predict", params={"country": "DE", "horizon": 4}).json()
    row = next(e for e in body["estimates"] if e["horizon"] == 4)
    assert row["probability"] == pytest.approx(live["probability"], abs=1e-12)
    assert row["version"] == live["model"]["id"]
    two = next(e for e in body["estimates"] if e["horizon"] == 2)
    assert two["probability"] is None and two["note"]
    assert any("4-quarter technical-recession model estimates" in s for s in body["summary"])


def test_in_sample_estimates_are_never_presented_as_forecasts(trained: TestClient) -> None:
    raw, _ = _report(trained, "json", as_of="2010-Q2")
    body = json.loads(raw)
    row = next(e for e in body["estimates"] if e["horizon"] == 4)
    assert row["note"].startswith("In-sample fit")
    sentence = next(s for s in body["summary"] if "4-quarter model" in s)
    assert "in-sample fit" in sentence
    assert "walk-forward estimate" in sentence
