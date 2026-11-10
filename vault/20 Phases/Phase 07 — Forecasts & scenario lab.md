---
type: phase
phase: 7
title: Forecasts & scenario lab
status: done
started: 2026-11-10
completed: 2026-11-10
tags:
  - phase
---

# Phase 7 — Forecasts & scenario lab

## Goal
Indicator forecasts with empirical intervals and bounded, non-causal sensitivity analysis.

## Acceptance (abridged — full list with evidence in `docs/ROADMAP.md`)
- [x] Naive baselines + stronger challenger with rolling backtests — naive, rolling mean, direct ridge AR; MAE, RMSE vs naive, bias per horizon ([[ADR-0017 Forecasts from rolling-origin backtests]])
- [x] Empirically justified intervals — past-error quantiles, coverage measured out of sample and shown; they under-cover ([[F-011 Forecast intervals under-cover]])
- [x] Scenario sliders change real calculations; non-causal disclaimer; OOD warnings — per-input range flags and a joint Mahalanobis check ([[ADR-0018 Scenario lab as bounded model sensitivity]])
- [x] Reset / save / export — URL state, localStorage saves with model version, JSON export

## Delivered
- `packages/ml/forecast.py` (`forecast-v1`), `services/forecasts.py`, `GET /api/forecasts`.
- `services/scenarios.py`, `GET /api/scenarios/spec`, `POST /api/scenarios/evaluate`; training now stores the feature covariance (run `20261110T142434Z`).
- In-process rate limit for both compute endpoints (`COMPUTE_REQUESTS_PER_MINUTE`, 429 + `Retry-After`).
- Web: Forecast studio (chart with ribbon and later-published values, projection table, diagnostics, backtest chart, assumptions, CSV/PNG) and Scenario lab (sliders, baseline vs scenario, contribution deltas, inputs table, saved scenarios, export).
- Shell fix: the country switcher no longer causes a hydration mismatch when the countries query resolves before it hydrates.

## Verified
217 pytest · 92 Vitest · ruff/mypy `--strict`/ESLint/tsc · `next build` · `pnpm smoke` 2105/2105 (all 15 forecast series, scenario round trip 5 × 2) · browser at 1440 px and 375 px (no horizontal overflow).

## Log
- 2026-11-10 — Forecast engine validated on real series (DE GDP, US unemployment) before any UI; ≤ 0.4 s per series.
- 2026-11-10 — Retrained to store the training covariance for the joint plausibility check.
- 2026-11-10 — API tests: no-look-ahead (truncated vs full run identical), coverage break test, as-of cut-off, scenario mapping, bounds; 25 tests.
- 2026-11-10 — Pre-existing hydration mismatch in the top-bar country switcher found and fixed (`useHydrated`).
- 2026-11-10 — Backtest across 15 series: AR coverage median 74 % (1Q) / 71 % (8Q), worst 50 % → [[F-011 Forecast intervals under-cover]].
- 2026-11-10 — Scenario lab shows the 4Q logistic model lowering risk when unemployment rises → [[F-012 Recession model lowers risk when unemployment rises]].
- 2026-11-10 — Added basic rate limiting before shipping the compute endpoints (CLAUDE.md §10).
- 2026-11-10 — Committed `ebfc4d4`; CI run 42838837827 green (Web, API, Docker images).
