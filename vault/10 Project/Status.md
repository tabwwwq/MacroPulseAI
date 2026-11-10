---
type: status
phase: 9
phase_name: Analyst-grade PDF reports
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
- ✅ **Phase 8 — Crisis time machine** done (2026-11-10): walk-forward replays with inputs as known then, outcomes as published later, warned / missed / false alarms; revised-data / release-lag approximation, no vintages. Most recessions were missed ([[F-013 Replays show most recessions were missed]]). See [[Phase 08 — Crisis time machine]].
- ⏭️ **Phase 9 — Analyst-grade PDF reports** is next. See [[Phase 09 — Analyst-grade PDF reports]].
- CI: run 42838837827 for `ebfc4d4` (Phase 7) passed all jobs — Web, API, Docker images. (Earlier: the Docker job failed on `ed7a1ab`, fixed in `b6987da` — [[F-010 Docker build broke when the ML package was added]].)

## Working (verified 2026-11-10)
- Data: 31 native series, 25,702 observations; BE/DE/FR/NL `full`, US `partial`.
- Models: run `20261110T142434Z` (retrained to store the feature covariance; same selection) — H=2 HistGradientBoosting, H=4 Logistic Regression; artifacts in `models/artifacts`.
- API: `/api/recession/predict` (round trip, explanation, track record, in-sample flag), `/api/recession/history`, `/api/models` + `/metrics` + `/curves`, `/api/forecasts`, `/api/scenarios/spec` + `POST /evaluate` (rate-limited), `/api/history/replay` + `/episodes` + `/presets`, plus all data endpoints.
- Web: Overview (live 2Q/4Q estimates with caveats), Countries, Compare, Data observatory, Recession risk, ML laboratory, Forecast studio, Scenario lab, **Crisis time machine**.
- Checks: 234 pytest (+1 PostgreSQL in CI, +16 live), 97 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`, `pnpm smoke` 2818/2818.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — shown next to every probability.
- [[F-009 Separate horizon models can contradict each other]] — flagged in the UI, not resolved.
- [[F-011 Forecast intervals under-cover]] — coverage shown and flagged, method unchanged.
- [[F-012 Recession model lowers risk when unemployment rises]] — visible in the scenario lab, not tuned away.
- [[F-013 Replays show most recessions were missed]] — 2Q warned 0 / 20, 4Q 6 / 22; listed per recession on `/history`.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector.
- No vintages / publication dates → replays stay *revised-data approximations*; `FRED_API_KEY` not configured → US `partial`.
- [[F-007 OneDrive locks the virtual environment]] — also stale dev-server reloads; restart servers after edits.
- Browser-level E2E tests not automated; Docker not installed locally (CI builds the images).

## Next
1. Phase 9: Report builder — a dated, print-friendly PDF (and CSV/JSON) per country with the overview KPIs and charts, the current model estimates with their track record (or the untrained state), forecasts with measured coverage, methodology, data citations with retrieval times, limitations and as-of dates; `POST /api/reports/generate` bounded and rate-limited.
