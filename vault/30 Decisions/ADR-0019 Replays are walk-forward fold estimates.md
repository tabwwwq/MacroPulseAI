---
type: decision
id: ADR-0019
date: 2026-11-10
status: accepted
area: ml
tags:
  - decision
---

# ADR-0019 · Replays are walk-forward fold estimates

> [!decision] Decision
> A replay of as-of quarter D in year Y shows the **stored walk-forward estimate** of the published model type: the model of fold Y, fitted only on as-of quarters t with t + H ≤ Y-Q1 − 1, whose outcomes were all published by the end of Y-Q1. The published model itself is never used for a past quarter, because it was fitted on that quarter's outcome. Every replay is labelled a **revised-data / release-lag approximation**.

## Why
- The published model's estimate for 2008 is an in-sample fit; a "time machine" built on it would show the model "predicting" what it was trained on. The fold estimates already exist (they are the backtest), are reproducible from the run, and need no artifact per fold.
- No vintages: Eurostat and the ECB serve the latest revision; ALFRED (US first releases) needs a server-side `FRED_API_KEY`, which is not configured, so vintage access could not be verified and is not claimed.

## Details
- **Inputs shown** are rebuilt with the training lags (GDP 60 d, inflation 30 d, unemployment 45 d, ECB decisions 0 d, FEDFUNDS 7 d, monthly rates 30 d) and show their reference period; the outcome window is shown as *published later*.
- **Leakage test:** deleting everything published after D reproduces the estimate of every model exactly; removing the horizon purge is detected ([[Phase 08 — Crisis time machine]]).
- **Honest residue:** for development years (2000–2014) the *choice* of model type used those years' backtests; the page says so. Held-out years (2015+) are clean of that too. The feature set and lags were designed in 2026.
- **Episodes:** a recession counts as *warned* when an estimate in the H − 1 as-of quarters before its first negative quarter reached 50 %; quarters before the first fold are *not evaluable*. False alarms are consecutive quarters ≥ 50 % with no recession following, tagged when they start during or within two quarters after a recession.
- **NBER** months (US) are shown as a separate external reference, never as the outcome.
- Quarters without a walk-forward estimate (before 2000-Q1, or 2002-Q1 for the 2-quarter model) answer 404 `replay_unavailable` with the reason; no in-sample number is offered instead.

## Consequences
The page shows the model's actual record, which is weak ([[F-013 Replays show most recessions were missed]]). True point-in-time replay remains possible later for the US only, with a verified ALFRED connection.

Related: [[ADR-0014 As-of cut-off over revised data]] · [[ADR-0016 Inference serving and explanations]] · [[F-008 No model beats the base rate on held-out years]]
