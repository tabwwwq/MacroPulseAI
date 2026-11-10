---
type: finding
id: F-011
severity: medium
status: open
area: ml
found: 2026-11-10
tags:
  - finding
---

# F-011 · Forecast intervals under-cover

> [!finding] Medium severity · open
> The nominal 80 % intervals of `forecast-v1` contain fewer than 80 % of later-published values in the rolling-origin backtest. Ridge AR, all 15 country/indicator series (API, 2026-11-10): **median coverage 74 % one quarter ahead and 71 % eight quarters ahead**; worst DE inflation at eight quarters, **50 %**. Coverage is measured honestly: each interval is built only from errors known at its origin.

## Evidence
| Series (8 quarters ahead) | AR coverage | Naive | Rolling mean |
|---|---|---|---|
| DE inflation | 50 % | 53 % | 49 % |
| US unemployment | 52 % | 54 % | 54 % |
| FR inflation | 56 % | 47 % | 47 % |
| US real GDP q/q | 86 % | 84 % | 85 % |

Accuracy: the AR beats the naive forecast one quarter ahead for 8 of 15 series and eight quarters ahead for 12 of 15; the rolling mean is often better for GDP growth and inflation at long horizons, and worse than naive for unemployment.

## Cause (likely)
Volatility is not stable: errors from calm decades set the quantiles, then the 2008–09 crisis, COVID-2020 and the 2021–23 inflation surge produce much larger misses. Empirical quantiles from all past errors adapt slowly.

## Action
Done: every coverage figure is shown with its count and flagged "under" when > 10 points below 80 %; the Projection card warns when the selected model under-covers at the chosen horizon; the assumptions say so. Possible later: recency-weighted or conformal intervals, accepted only if backtest coverage improves.

Related: [[ADR-0017 Forecasts from rolling-origin backtests]] · [[Phase 07 — Forecasts & scenario lab]]
