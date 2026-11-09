---
type: methodology
status: planned
tags:
  - methodology
  - ml
---

# 🧪 Evaluation protocol

> [!warning] Planned for Phase 5 — nothing here has been run yet. No metrics exist.

## Splits
- Walk-forward / expanding window; **never** random splits.
- Purge gap ≥ H quarters between train and validation/test so labels do not overlap.
- Pooled countries are split on **time**, not by country, to avoid cross-country temporal leakage.
- Final test period held out until the end.

## Leakage guards
- Scalers and imputers fit on training folds only.
- Features use only data published by the `as_of` date (conservative release lags; vintages where available).
- Annual inputs: the latest *already published* value with a staleness flag.

## Models (in order)
1. Unconditional prevalence and simple threshold baselines
2. Logistic Regression (scaled, regularised)
3. HistGradientBoosting / XGBoost if installed
4. Calibration (isotonic / sigmoid) on a disjoint temporal split when samples allow
5. LSTM/GRU only as a research comparison if sample counts justify it

## Metrics
Brier score, log loss, calibration curve, PR-AUC, ROC-AUC when defined, confusion matrix at a stated threshold, sample and event counts. If a window contains one class only, report **N/A** — never a fake metric. Accuracy alone is misleading when most quarters are non-recession.

Related: [[Technical recession target]]
