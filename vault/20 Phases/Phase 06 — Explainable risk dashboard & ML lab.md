---
type: phase
phase: 6
title: Explainable risk dashboard & ML lab
status: done
started: 2026-11-09
completed: 2026-11-10
tags:
  - phase
---

# Phase 6 — Explainable risk dashboard & ML lab

## Goal
Expose real evaluated inference on `/recession` and diagnostics on `/lab`.

## Acceptance (abridged — full list in `docs/ROADMAP.md`)
- [x] 2Q/4Q horizon switch, model version, as-of date, probability from a live round trip
- [x] Documented fallback contributions (SHAP not installed): exact log-odds for logistic, local sensitivity for trees
- [x] Split timeline, calibration, ROC/PR where valid, baseline comparison, sample sizes
- [x] Actionable unavailable states; validation tests for unsupported countries/horizons

## What was built
- **API:** `services/inference.py` (as-of snapshot from stored data → joblib artifact loaded only from `MODELS_DIR` → probability, band, base rate, explanation, track record, in-sample flag, walk-forward estimate, realised outcome); `GET /api/recession/predict`, `GET /api/recession/history`, `GET /api/models/{id}/curves`. Training now stores the feature distribution of the final sample (used for explanations and range warnings).
- **Web:** `/recession` — gauge with bands and base-rate tick, model facts and round-trip check, warnings (held-out, in-sample, P(4Q) < P(2Q)), contributions, walk-forward risk timeline with realised recessions, track record, definition, limitations. `/lab` — comparison of every model, calibration, ROC and PR curves, confusion matrices, per-country metrics, fold timeline, logistic coefficients, reproducibility card. Overview KPI tile and risk card show the live estimate with the same caveats.
- **Ops:** API Dockerfile copies `packages/ml` and keeps artifacts on a `models` volume ([[F-010 Docker build broke when the ML package was added]]).
- Decision: [[ADR-0016 Inference serving and explanations]].

## Verified
185 pytest (12 inference/round-trip/artifact-safety tests) · 79 Vitest · ruff / mypy `--strict` / ESLint / tsc · `next build` · `pnpm smoke` 495/495 (round trip 5 countries × 2 horizons) · pages checked in the browser and as headless-Edge screenshots of the production build.

> [!example] Honest read-outs from the live data (run 20261109T182857Z)
> - DE, 4 quarters, as of 2026-Q3: **18.3 %** (moderate), base rate 15.5 %; top contributions: term spread +0.30, inflation change +0.20 log-odds.
> - US, 4 quarters, as of 2008-Q2: final model 10.7 % but flagged *in-sample*; the walk-forward estimate made at the time was **1.9 %** and a recession followed — a miss, shown as such.
> - FR: 2Q 20.9 % vs 4Q 14.2 % → logical contradiction flagged ([[F-009 Separate horizon models can contradict each other]]).

## Log
- 2026-11-09 — Inference service, recession/curves endpoints, 12 API tests (one shared training run: 95 s → 14 s).
- 2026-11-09 — `Literal[2, 4]` query param did not coerce from strings → explicit horizon check with `unsupported_horizon`.
- 2026-11-09 — Recession page, ML lab, risk summary on the overview; empty-country query (422) fixed with `enabled`.
- 2026-11-10 — Found that CI for `ed7a1ab` had failed in the Docker job (missing `packages/ml`), reproduced without Docker, fixed.
