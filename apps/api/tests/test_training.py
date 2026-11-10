"""Training service persistence and the read-only model API.

The panel is synthetic (injected through `load_inputs`) because CI has no synced official data; it
exercises storage and reproducibility metadata, never model quality.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from macropulse_api.errors import ApiError
from macropulse_api.models import ModelMetric, ModelPrediction, ModelVersion
from macropulse_api.services import training
from macropulse_ml.features import FEATURE_NAMES, CountryInputs

from .fixture_sources import synthetic_country_inputs


@pytest.fixture
def synthetic(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_load(_session: object) -> tuple[list[CountryInputs], dict[str, str], str]:
        return (
            [synthetic_country_inputs("DE", 1), synthetic_country_inputs("US", 2)],
            {"FR": "test: not loaded"},
            "sha256:test",
        )

    monkeypatch.setattr(training, "load_inputs", fake_load)


def test_training_requires_stored_inputs(app: FastAPI) -> None:
    with pytest.raises(ApiError) as info:
        training.train(app.state.sessionmaker, horizons=(4,), today=date(2026, 11, 9))
    assert info.value.code == "data_not_synced"


def test_training_persists_versions_metrics_predictions_and_artifact(
    app: FastAPI, client: TestClient, synthetic: None, tmp_path: Path
) -> None:
    assert client.get("/api/models").json()["items"] == []
    report = training.train(
        app.state.sessionmaker,
        horizons=(4,),
        seed=7,
        artifacts_root=tmp_path,
        command="uv run macropulse train --horizon 4 --seed 7",
        code_revision="abc1234",
        today=date(2026, 11, 9),
    )
    with app.state.sessionmaker() as s:
        versions = s.scalars(select(ModelVersion).where(ModelVersion.run_id == report.run_id)).all()
        assert {v.model_key for v in versions} == {
            "prevalence",
            "contraction_rule",
            "logistic",
            "hist_gbm",
            "hist_gbm_platt",
            "xgboost",
        }
        selected = [v for v in versions if v.selected]
        assert len(selected) == 1
        sel = selected[0]
        assert sel.artifact_path is not None
        assert sel.training_rows and sel.training_events
        assert sel.feature_names == list(FEATURE_NAMES)
        assert sel.data_snapshot == "sha256:test"
        assert sel.code_revision == "abc1234"
        assert sel.seed == 7
        assert "heldout_check" in sel.evaluation and "selection_note" in sel.evaluation
        assert sel.label_cutoff == {"DE": "2026-Q3", "US": "2026-Q3"}
        assert all(v.artifact_path is None for v in versions if not v.selected)

        live = s.scalars(
            select(ModelPrediction).where(
                ModelPrediction.model_version_id == sel.id, ModelPrediction.split == "live"
            )
        ).all()
        assert {p.country for p in live} == {"DE", "US"}
        assert all(p.as_of == "2026-Q3" and 0 <= p.probability <= 1 for p in live)
        oos = s.scalar(
            select(func.count())
            .select_from(ModelPrediction)
            .where(ModelPrediction.model_version_id == sel.id, ModelPrediction.split != "live")
        )
        assert oos and oos > 100
        undefined = s.scalars(select(ModelMetric).where(ModelMetric.value.is_(None))).all()
        assert all(m.note or m.detail is not None for m in undefined)

    artifact = Path(sel.artifact_path)
    model = joblib.load(artifact / "model.joblib")
    assert model.predict_proba(np.zeros((1, len(FEATURE_NAMES)))).shape == (1, 2)
    meta = json.loads((artifact / "metadata.json").read_text(encoding="utf-8"))
    assert meta["model_version"] == sel.id
    assert meta["command"].startswith("uv run macropulse train")
    assert meta["events_in_data"]["DE"]


def test_model_api_lists_and_details_measured_metrics(
    app: FastAPI, client: TestClient, synthetic: None
) -> None:
    training.train(app.state.sessionmaker, horizons=(4,), seed=7, today=date(2026, 11, 9))
    body = client.get("/api/models").json()
    assert body["run_id"]
    items = {i["model_key"]: i for i in body["items"]}
    selected = [i for i in body["items"] if i["selected"]]
    assert len(selected) == 1
    assert selected[0]["selection_note"]
    assert selected[0]["heldout_check"]["evaluated"] is True
    assert set(items["logistic"]["headline"]) == {"development", "heldout"}
    if items["xgboost"]["status"] != "evaluated":
        assert "not installed" in items["xgboost"]["unavailable_reason"]

    detail = client.get(f"/api/models/{selected[0]['id']}/metrics").json()
    assert detail["feature_names"] == list(FEATURE_NAMES)
    kinds = {m["metric"] for m in detail["metrics"]}
    assert {"brier", "log_loss", "roc_auc", "pr_auc", "calibration", "confusion"} <= kinds
    calibration = next(m for m in detail["metrics"] if m["metric"] == "calibration")
    assert sum(b["count"] for b in calibration["detail"]) == calibration["n"]
    assert detail["evaluation"]["purge"].startswith("training labels must end")


@pytest.mark.parametrize(
    ("model_id", "status"),
    [("20990101T000000Z-h4-logistic", 404), ("not-a-model", 422), ("20990101T000000Z-h3-x", 422)],
)
def test_model_detail_errors(client: TestClient, model_id: str, status: int) -> None:
    assert client.get(f"/api/models/{model_id}/metrics").status_code == status
