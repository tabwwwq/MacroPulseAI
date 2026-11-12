"""Re-fit one walk-forward fold model exactly as the backtest did.

The backtest stores predictions, not the per-year fold models. To score *other* inputs for a past
as-of quarter (e.g. the figures as first published), the fold model of that year is fitted again
from the same panel, training rows, specification and seed. Callers must check that the re-fitted
model reproduces the stored walk-forward estimate before trusting it.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from macropulse_ml.backtest import FIRST_TEST_YEAR, _fit
from macropulse_ml.features import FEATURE_NAMES
from macropulse_ml.models import SPECS, Classifier
from macropulse_ml.panel import Panel
from macropulse_ml.splits import walk_forward


def fold_model(
    panel: Panel, horizon: int, model_key: str, seed: int, fold_year: int
) -> Classifier | None:
    """The model the backtest fitted for `fold_year`, or None when that fold was skipped."""
    spec = next((s for s in SPECS if s.key == model_key), None)
    if spec is None:
        raise KeyError(model_key)
    folds, _ = walk_forward(panel, horizon, FIRST_TEST_YEAR, fold_year)
    fold = next((f for f in folds if f.year == fold_year), None)
    if fold is None:
        return None
    model, _ = _fit(spec, seed, panel, fold.train, horizon)
    return model


def predict_one(model: Classifier, values: Mapping[str, float]) -> float:
    """Probability for one snapshot's feature values (in FEATURE_NAMES order)."""
    x = np.array([[values[name] for name in FEATURE_NAMES]], dtype=np.float64)
    return float(np.asarray(model.predict_proba(x), dtype=np.float64)[0, 1])
