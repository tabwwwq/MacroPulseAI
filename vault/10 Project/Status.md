---
type: status
phase: 7
phase_name: Forecasts & scenario lab
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
- ⏭️ **Phase 7 — Forecasts & scenario lab** is next. See [[Phase 07 — Forecasts & scenario lab]].
- CI: the Docker job failed on `ed7a1ab`; fixed in `b6987da`, whose CI run passed all jobs including Docker images ([[F-010 Docker build broke when the ML package was added]]).

## Working (verified 2026-11-10)
- Data: 31 native series, 25,702 observations; BE/DE/FR/NL `full`, US `partial`.
- Models: run `20261109T182857Z` — H=2 HistGradientBoosting, H=4 Logistic Regression; artifacts in `models/artifacts`.
- API: `/api/recession/predict` (round trip, explanation, track record, in-sample flag), `/api/recession/history`, `/api/models` + `/metrics` + `/curves`, plus all data endpoints.
- Web: Overview (live 2Q/4Q estimates with caveats), Countries, Compare, Data observatory, **Recession risk**, **ML laboratory**.
- Checks: 185 pytest (+1 PostgreSQL in CI, +16 live), 79 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`, `pnpm smoke` 495/495.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — shown next to every probability.
- [[F-009 Separate horizon models can contradict each other]] — flagged in the UI, not resolved.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector.
- No vintages / publication dates → replays stay *revised-data approximations*; `FRED_API_KEY` not configured → US `partial`.
- [[F-007 OneDrive locks the virtual environment]] — also stale dev-server reloads; restart servers after edits.
- Browser-level E2E tests not automated; Docker not installed locally (CI builds the images).

## Next
1. Phase 7: GDP growth / inflation / unemployment forecasts — naive and seasonal-naive baselines plus a challenger, rolling-origin backtests, empirical intervals; Scenario lab with bounded sliders, baseline vs scenario risk, contribution deltas and out-of-distribution warnings (training feature ranges are already stored).
