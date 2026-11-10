---
type: decision
id: ADR-0017
date: 2026-11-10
status: accepted
area: ml
tags:
  - decision
---

# ADR-0017 · Forecasts from rolling-origin backtests

> [!decision] Decision
> Indicator forecasts come from three fixed, deterministic models — **naive** (last value), **rolling mean** (20 quarters / 60 months) and a **direct ridge AR** (one regression per step on the latest 4 quarters / 6 months, refitted at every origin) — each scored in a rolling-origin backtest over every past origin. The 80 % interval is the forecast plus the 10th/90th percentile of that model's **own past errors at that step**, and its coverage is measured with intervals built only from errors already known at each origin.

## Why
- The naive forecast is the reference every model must beat; the rolling mean is a mean-reversion baseline; the AR is the simplest challenger that can exploit persistence. No ARIMA order search or boosted lags: model selection on 15 short series would overfit the backtest.
- No seasonal-naive baseline: the GDP series are seasonally adjusted and inflation is a year-on-year rate.
- Empirical error quantiles need no distributional assumption and can be checked: the backtest reports how often later-published values fell inside, per horizon, instead of asserting 80 %.

## Details
- Inputs: stored official series on a contiguous period grid; missing values stay NaN (AR unavailable when the latest lags are incomplete — the reason is shown).
- Past as-of: only observations with `period_end + publication lag ≤ cut-off` (same lags as the recession features, [[ADR-0014 As-of cut-off over revised data]]); later values come back as `realised`. Revised data, not vintages.
- Intervals are withheld until 20 scored errors exist for a step. "Under-coverage" is flagged when measured coverage is more than 10 points below nominal.
- The default model in the UI is the AR (pre-specified), not the lowest backtest RMSE; the table marks the lowest RMSE and says that choice is optimistic.
- Results are cached in process per stored series, retrieval time and origin; horizons share one run.

## Consequences
The page shows that the intervals are too narrow (median coverage 71–74 %, worst 50 %) and that the AR often does not beat the naive forecast one quarter ahead — see [[F-011 Forecast intervals under-cover]]. Better calibrated intervals (e.g. conformal with recency weighting) are a possible later change, judged on the same backtest.

Related: [[Phase 07 — Forecasts & scenario lab]] · [[ADR-0018 Scenario lab as bounded model sensitivity]]
