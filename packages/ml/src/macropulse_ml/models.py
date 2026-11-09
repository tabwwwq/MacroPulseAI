"""Model registry: reference baselines, Logistic Regression and boosted-tree challengers.

Hyperparameters are fixed in advance (no tuning on test data) and recorded with every artifact.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

Matrix = NDArray[np.float64]
Labels = NDArray[np.int64]
EPS = 1e-6


class Classifier(Protocol):
    def fit(self, x: Matrix, y: Labels) -> Classifier: ...

    def predict_proba(self, x: Matrix) -> Any: ...


class Prevalence:
    """Unconditional training event rate — the reference every model must beat."""

    def __init__(self) -> None:
        self.p = 0.0

    def fit(self, x: Matrix, y: Labels) -> Prevalence:
        self.p = float(np.mean(y))
        return self

    def predict_proba(self, x: Matrix) -> Matrix:
        p = np.full(len(x), self.p)
        return np.column_stack([1 - p, p])


class ContractionRule:
    """Interpretable threshold baseline: event rate given whether the latest published quarter
    contracted (Laplace-smoothed frequencies from the training window)."""

    def __init__(self, column: int = 0) -> None:
        self.column = column
        self.p_neg = 0.0
        self.p_pos = 0.0

    def fit(self, x: Matrix, y: Labels) -> ContractionRule:
        neg = x[:, self.column] < 0
        self.p_neg = float((y[neg].sum() + 1) / (neg.sum() + 2))
        self.p_pos = float((y[~neg].sum() + 1) / ((~neg).sum() + 2))
        return self

    def predict_proba(self, x: Matrix) -> Matrix:
        p = np.where(x[:, self.column] < 0, self.p_neg, self.p_pos)
        return np.column_stack([1 - p, p])


class PlattCalibrated:
    """Fit the base model on the earlier part of the training window and a sigmoid calibrator on a
    later, disjoint part (separated by the horizon purge). Used only when the calibration slice has
    enough events of both classes; otherwise the raw model is returned and the fact is recorded."""

    def __init__(self, base: Callable[[], Classifier], min_events: int = 6) -> None:
        self.base_factory = base
        self.min_events = min_events
        self.model: Classifier | None = None
        self.calibrator: LogisticRegression | None = None
        self.calibrated = False

    def fit_temporal(
        self, x: Matrix, y: Labels, q: NDArray[np.int64], horizon: int
    ) -> PlattCalibrated:
        order = np.argsort(q, kind="stable")
        cut_q = q[order[int(len(order) * 0.7)]]
        fit_mask = q <= cut_q - horizon - 1
        cal_mask = q >= cut_q
        y_cal = y[cal_mask]
        enough = (
            fit_mask.sum() > 0
            and y_cal.sum() >= self.min_events
            and (len(y_cal) - y_cal.sum()) >= self.min_events
            and 0 < y[fit_mask].sum() < fit_mask.sum()
        )
        self.model = self.base_factory()
        if not enough:
            self.model.fit(x, y)
            self.calibrated = False
            return self
        self.model.fit(x[fit_mask], y[fit_mask])
        raw = np.clip(self.model.predict_proba(x[cal_mask])[:, 1], EPS, 1 - EPS)
        self.calibrator = LogisticRegression(C=1e6, max_iter=1000)
        self.calibrator.fit(np.log(raw / (1 - raw)).reshape(-1, 1), y_cal)
        self.calibrated = True
        return self

    def fit(self, x: Matrix, y: Labels) -> PlattCalibrated:  # pragma: no cover - use fit_temporal
        raise TypeError("PlattCalibrated needs as-of quarters; call fit_temporal")

    def predict_proba(self, x: Matrix) -> Matrix:
        if self.model is None:
            raise RuntimeError("not fitted")
        raw = np.clip(self.model.predict_proba(x)[:, 1], EPS, 1 - EPS)
        if not self.calibrated or self.calibrator is None:
            p = raw
        else:
            p = self.calibrator.predict_proba(np.log(raw / (1 - raw)).reshape(-1, 1))[:, 1]
        return np.column_stack([1 - p, p])


def logistic(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", LogisticRegression(C=0.5, max_iter=5000, random_state=seed)),
        ]
    )


def boosted(seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_depth=3,
        learning_rate=0.05,
        max_iter=200,
        min_samples_leaf=20,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=seed,
    )


def xgboost_available() -> bool:
    return importlib.util.find_spec("xgboost") is not None


def xgb(seed: int) -> Classifier:  # pragma: no cover - optional dependency
    from xgboost import XGBClassifier  # noqa: PLC0415 - optional import

    model: Classifier = XGBClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        min_child_weight=5,
        reg_lambda=1.0,
        eval_metric="logloss",
        random_state=seed,
    )
    return model


@dataclass(frozen=True)
class ModelSpec:
    key: str
    name: str
    role: str  # "baseline" | "candidate"
    params: dict[str, Any] = field(default_factory=dict)
    calibrated: bool = False


SPECS: tuple[ModelSpec, ...] = (
    ModelSpec("prevalence", "Unconditional prevalence", "baseline"),
    ModelSpec(
        "contraction_rule", "Latest-quarter contraction rule", "baseline", {"feature": "gdp_qoq_1"}
    ),
    ModelSpec("logistic", "Logistic Regression (L2, standardised)", "candidate", {"C": 0.5}),
    ModelSpec(
        "hist_gbm",
        "HistGradientBoosting",
        "candidate",
        {"max_depth": 3, "learning_rate": 0.05, "max_iter": 200, "min_samples_leaf": 20, "l2": 1.0},
    ),
    ModelSpec(
        "hist_gbm_platt",
        "HistGradientBoosting + temporal Platt calibration",
        "candidate",
        {"calibration_share": 0.3, "min_calibration_events": 6},
        calibrated=True,
    ),
    ModelSpec(
        "xgboost",
        "XGBoost",
        "candidate",
        {"max_depth": 3, "learning_rate": 0.05, "n_estimators": 200, "subsample": 0.8},
    ),
)


def make(key: str, seed: int) -> Classifier:
    if key == "prevalence":
        return Prevalence()
    if key == "contraction_rule":
        return ContractionRule(column=0)
    if key == "logistic":
        model: Classifier = logistic(seed)
        return model
    if key == "hist_gbm":
        tree: Classifier = boosted(seed)
        return tree
    if key == "xgboost":
        return xgb(seed)
    raise KeyError(key)
