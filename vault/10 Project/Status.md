---
type: status
phase: 8
phase_name: Crisis time machine
updated: 2026-11-10
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** done (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- ✅ **Phase 2 — Production-grade UI system** done (2026-11-09). See [[Phase 02 — Production-grade UI system]].
- ✅ **Phase 3 — Economic data ingestion & metadata** done (`90e0e91`, 2026-11-09). See [[Phase 03 — Economic data ingestion & metadata]].
- ✅ **Phase 4 — Data coverage & real dashboards** done (`51fb279`, 2026-11-09). See [[Phase 04 — Data coverage & real dashboards]].
- ✅ **Phase 5 — Recession target, features & first model** done (`ed7a1ab`, 2026-11-09) — published models do **not** beat the base rate on 2015+ held-out years ([[F-008 No model beats the base rate on held-out years]]). See [[Phase 05 — Recession target, features & first model]].
- ✅ **Phase 6 — Explainable risk dashboard & ML lab** done (2026-11-10): live inference round trip, explanations, risk timeline, ML laboratory. See [[Phase 06 — Explainable risk dashboard & ML lab]].
- ✅ **Phase 7 — Forecasts & scenario lab** done (2026-11-10): rolling-origin forecasts with measured interval coverage, scenario lab with bounded shocks and plausibility checks. Intervals under-cover ([[F-011 Forecast intervals under-cover]]). See [[Phase 07 — Forecasts & scenario lab]].
- ⏭️ **Phase 8 — Crisis time machine** is next. See [[Phase 08 — Crisis time machine]].
- CI: the Docker job failed on `ed7a1ab`; fixed in `b6987da`, whose CI run passed all jobs including Docker images ([[F-010 Docker build broke when the ML package was added]]).

## Working (verified 2026-11-10)
- Data: 31 native series, 25,702 observations; BE/DE/FR/NL `full`, US `partial`.
- Models: run `20261110T142434Z` (retrained to store the feature covariance; same selection) — H=2 HistGradientBoosting, H=4 Logistic Regression; artifacts in `models/artifacts`.
- API: `/api/recession/predict` (round trip, explanation, track record, in-sample flag), `/api/recession/history`, `/api/models` + `/metrics` + `/curves`, `/api/forecasts`, `/api/scenarios/spec` + `POST /evaluate` (rate-limited), plus all data endpoints.
- Web: Overview (live 2Q/4Q estimates with caveats), Countries, Compare, Data observatory, Recession risk, ML laboratory, **Forecast studio**, **Scenario lab**.
- Checks: 217 pytest (+1 PostgreSQL in CI, +16 live), 92 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`, `pnpm smoke` 2105/2105.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — shown next to every probability.
- [[F-009 Separate horizon models can contradict each other]] — flagged in the UI, not resolved.
- [[F-011 Forecast intervals under-cover]] — coverage shown and flagged, method unchanged.
- [[F-012 Recession model lowers risk when unemployment rises]] — visible in the scenario lab, not tuned away.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector.
- No vintages / publication dates → replays stay *revised-data approximations*; `FRED_API_KEY` not configured → US `partial`.
- [[F-007 OneDrive locks the virtual environment]] — also stale dev-server reloads; restart servers after edits.
- Browser-level E2E tests not automated; Docker not installed locally (CI builds the images).

## Next
1. Phase 8: Crisis time machine — pick a country and an as-of quarter (e.g. 2007, 2020, 2022), show only what was known then (features, and the walk-forward fold model trained without later outcomes), compare with what happened, and mark every replay as a revised-data / release-lag approximation; ALFRED vintages for the US only if `FRED_API_KEY` is configured and verified.
