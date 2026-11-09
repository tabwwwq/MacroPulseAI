"""Probabilistic evaluation. A metric that is undefined for the data (one class only, no predicted
positives) is returned as `None` with a reason — never as a number."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import average_precision_score, roc_auc_score

EPS = 1e-6
THRESHOLD = 0.5  # "more likely than not"; precision/recall/confusion are reported at this value
CALIBRATION_EDGES = (0.0, 0.1, 0.2, 0.4, 0.6, 1.0)


@dataclass
class MetricSet:
    n: int
    events: int
    values: dict[str, float | None] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    calibration: list[dict[str, Any]] = field(default_factory=list)
    confusion: dict[str, int] = field(default_factory=dict)


def evaluate(
    y: NDArray[np.int64], p: NDArray[np.float64], reference: NDArray[np.float64] | None = None
) -> MetricSet:
    y = np.asarray(y, dtype=np.int64)
    p = np.clip(np.asarray(p, dtype=np.float64), 0.0, 1.0)
    n, events = len(y), int(y.sum())
    m = MetricSet(n=n, events=events)
    if n == 0:
        m.notes["all"] = "No labelled observations in this split."
        return m

    brier = float(np.mean((p - y) ** 2))
    pc = np.clip(p, EPS, 1 - EPS)
    m.values["brier"] = brier
    m.values["log_loss"] = float(-np.mean(y * np.log(pc) + (1 - y) * np.log(1 - pc)))
    m.values["prevalence"] = events / n
    m.values["mean_probability"] = float(np.mean(p))

    if 0 < events < n:
        m.values["roc_auc"] = float(roc_auc_score(y, p))
        m.values["pr_auc"] = float(average_precision_score(y, p))
    else:
        reason = "Only one class in this split."
        m.values["roc_auc"] = m.values["pr_auc"] = None
        m.notes["roc_auc"] = m.notes["pr_auc"] = reason

    if reference is not None:
        ref_brier = float(np.mean((np.clip(reference, 0, 1) - y) ** 2))
        m.values["brier_reference"] = ref_brier
        if ref_brier > 0:
            m.values["brier_skill"] = 1 - brier / ref_brier
        else:
            m.values["brier_skill"] = None
            m.notes["brier_skill"] = "Reference Brier score is zero."

    pred = p >= THRESHOLD
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1)))
    tn = int(np.sum(~pred & (y == 0)))
    m.confusion = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    m.values["threshold"] = THRESHOLD
    if tp + fp:
        m.values["precision"] = tp / (tp + fp)
    else:
        m.values["precision"] = None
        m.notes["precision"] = f"No probability reached {THRESHOLD}."
    if events:
        m.values["recall"] = tp / events
    else:
        m.values["recall"] = None
        m.notes["recall"] = "No events in this split."
    m.values["accuracy"] = (tp + tn) / n

    edges = CALIBRATION_EDGES
    for lo, hi in pairwise(edges):
        in_bin = (p >= lo) & ((p < hi) if hi < 1.0 else (p <= hi))
        count = int(in_bin.sum())
        m.calibration.append(
            {
                "bin": [lo, hi],
                "count": count,
                "mean_predicted": float(p[in_bin].mean()) if count else None,
                "observed_rate": float(y[in_bin].mean()) if count else None,
                "events": int(y[in_bin].sum()),
            }
        )
    return m
