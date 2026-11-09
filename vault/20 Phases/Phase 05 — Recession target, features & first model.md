---
type: phase
phase: 5
title: Recession target, features & first model
status: done
started: 2026-11-09
completed: 2026-11-09
tags:
  - phase
---

# Phase 5 — Recession target, features & first model

## Goal
Reproduce technical-recession labels and horizon-safe temporal backtests with honest metrics.

## Acceptance (abridged — full list in `docs/ROADMAP.md`)
- [x] H=2/4 labels per [[Technical recession target]]; censoring of unobservable labels
- [x] As-of quarterly features with conservative release lags
- [x] Prevalence baseline, Logistic Regression, boosted-tree challenger (HistGradientBoosting; XGBoost recorded as not installed)
- [x] Brier, log loss, ROC/PR-AUC (N/A when undefined), calibration; leakage tests

## What was built
- `packages/ml`: `target.py` (labels, event dating), `features.py` (as-of snapshots, lags, staleness), `panel.py`, `splits.py` (yearly purged walk-forward), `models.py`, `metrics.py`, `backtest.py` (scoring, selection, final fit).
- API: migration `0003` (`model_versions`, `model_metrics`, `model_predictions`), `services/training.py`, CLI `uv run macropulse train` / `pnpm train`, read-only `GET /api/models` and `/api/models/{id}/metrics`.
- Data: 10-year yields (Eurostat `irt_lt_mcby_m`, FRED `GS10`) and 3-month rates (Eurostat `irt_st_m` euro area, FRED `TB3MS`) → 31 series, 25,702 observations.
- Artifacts: `models/artifacts/<run>/h<H>/model.joblib + metadata.json` (git-ignored).
- Decisions: [[ADR-0015 Publish only what beats the baseline]].

## Result (run 20261109T173231Z)
| H | published | development skill | held-out skill | current estimates as of 2026-Q3 |
| --- | --- | --- | --- | --- |
| 2 | HistGradientBoosting | +0.099 | **−0.448** | BE 4 %, DE 4 %, FR 21 %, NL 2 %, US 1 % |
| 4 | Logistic Regression | +0.032 | **−0.754** | BE 25 %, DE 18 %, FR 14 %, NL 15 %, US 17 % |

> [!warning] Honest bottom line
> Real but small skill on 2000–2014; **no skill against the base rate on 2015–2026** → [[F-008 No model beats the base rate on held-out years]]. The estimates above are shown in the product only with that track record.

## Verified (2026-11-09)
173 pytest (30 ML: labels, leakage, purge, scaler, selection, reproducibility) · 73 Vitest · ruff / mypy `--strict` / ESLint / tsc · `next build` · real training run in 17 s · `pnpm smoke` 416/416 · 16 live API tests.

## Log
- 2026-11-09 — Phase 4 pushed (`51fb279`), CI green.
- 2026-11-09 — First run (v1 features): selection rule picked an H=4 model that lost to the baseline on development → rule fixed (ADR-0015).
- 2026-11-09 — Development diagnosis: v1 features are coincident (2008 mean p 0.12 with 17/20 events) → term spread added from official rates for all countries (feature set v2).
- 2026-11-09 — Smoke test caught `/api/indicators` rejecting ids with digits (`bond_yield_10y`) → pattern fixed, regression test added.
- 2026-11-09 — UI copy that said "no trained model" now follows `/api/models` and states the held-out result.
