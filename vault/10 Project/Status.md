---
type: status
phase: 6
phase_name: Explainable risk dashboard & ML lab
updated: 2026-11-09
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** done (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- ✅ **Phase 2 — Production-grade UI system** done (2026-11-09). See [[Phase 02 — Production-grade UI system]].
- ✅ **Phase 3 — Economic data ingestion & metadata** done (`90e0e91`, 2026-11-09). See [[Phase 03 — Economic data ingestion & metadata]].
- ✅ **Phase 4 — Data coverage & real dashboards** done (`51fb279`, 2026-11-09). See [[Phase 04 — Data coverage & real dashboards]].
- ✅ **Phase 5 — Recession target, features & first model** done (2026-11-09): labels, as-of features, walk-forward backtest, published models — **with no skill against the base rate on 2015–2026** ([[F-008 No model beats the base rate on held-out years]]). See [[Phase 05 — Recession target, features & first model]].
- ⏭️ **Phase 6 — Explainable risk dashboard & ML lab** is next. See [[Phase 06 — Explainable risk dashboard & ML lab]].
- Repository: GitHub `tabwwwq/MacroPulseAI`; CI green on `51fb279`.

## Working (verified 2026-11-09)
- Data: `pnpm data:sync` — 31 native series, 25,702 observations (Eurostat 21, ECB 1, FRED 9 series). BE/DE/FR/NL `full`, US `partial`.
- Models: `pnpm train` — run `20261109T173231Z`: H=2 HistGradientBoosting (dev skill +0.099, held-out −0.448), H=4 Logistic Regression (+0.032, −0.754); artifacts with metadata; `/api/models` read-only.
- API/web: dashboards on stored data with provenance; model state shown truthfully (no probability displayed before Phase 6).
- Checks: 173 pytest (+1 PostgreSQL in CI, +16 live), ruff, mypy `--strict`, ESLint, tsc, 73 Vitest, `next build`, `pnpm smoke` 416/416.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — probabilities need a prominent track-record warning; held-out period no longer pristine.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule (tested).
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector; fewer leading indicators.
- No vintages / publication dates → replays stay *revised-data approximations*.
- FRED metadata and ALFRED vintages need a server-side `FRED_API_KEY` → US stays `partial`.
- [[F-007 OneDrive locks the virtual environment]]; uvicorn `--reload` does not see OneDrive edits (restart the API after code changes).
- Browser-level E2E tests not automated; Docker not installed locally.

## Next
1. Phase 6: `/api/recession/predict` and `/history` from stored predictions and the saved artifact (round trip), 2Q/4Q selector, probability with model version / as-of / track record, risk timeline (OOS backtest + current), explanations (standardised coefficients / permutation importance), ML lab with comparison table, calibration and confusion views, reproducibility card.
