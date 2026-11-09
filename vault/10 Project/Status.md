---
type: status
phase: 5
phase_name: Recession target, features & first model
updated: 2026-11-09
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** done (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- ✅ **Phase 2 — Production-grade UI system** done (2026-11-09). See [[Phase 02 — Production-grade UI system]].
- ✅ **Phase 3 — Economic data ingestion & metadata** done (`90e0e91`, 2026-11-09): **21,094 real observations** from Eurostat, ECB and FRED. See [[Phase 03 — Economic data ingestion & metadata]].
- ✅ **Phase 4 — Data coverage & real dashboards** done (2026-11-09): Overview, Country Explorer, Compare and Data Observatory plot the stored series with provenance. See [[Phase 04 — Data coverage & real dashboards]].
- ⏭️ **Phase 5 — Recession target, features & first model** is next. See [[Phase 05 — Recession target, features & first model]].
- Repository: GitHub `tabwwwq/MacroPulseAI`; CI green on `90e0e91`.
- No model is trained — the risk widgets say so and explain why.

## Working (verified 2026-11-09)
- Data: `pnpm data:sync` fetches 24 native series (Eurostat 16, ECB 1, FRED 7) with retries, quality checks and idempotent upserts ([[ADR-0013 Native-series ingestion with quality gate]]). Support levels from stored data: BE, DE, FR, NL `full`; US `partial`.
- API: countries, sources/status, indicators/catalog, `/api/indicators`, **`/api/countries/{iso2}/summary`** (as-of cut-off — [[ADR-0014 As-of cut-off over revised data]]), **data-quality** inventory, **raw CSV export**; error contract; request ids; JSON logs.
- Web: KPI tiles with value, change, flags and provenance; charts with hover source, history window, as-of cut-off, NBER reference bands (US), CSV with citations; compare as published or spread vs baseline; lineage with quality checks.
- Checks: 136 pytest (+1 PostgreSQL in CI, +12 opt-in live tests), ruff, mypy `--strict`, ESLint, tsc, 70 Vitest, `next build`, `pnpm smoke` 348/348.

## Blockers & risks
- [[F-006 US October 2025 observations missing]] — Phase 5 needs an explicit monthly → quarterly aggregation rule (minimum months per quarter).
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector yet; reduced feature set for BE/NL.
- No vintages / publication dates → features need documented conservative release lags; replays stay *revised-data approximations*.
- FRED metadata and ALFRED vintages need a server-side `FRED_API_KEY` (not configured) → US stays `partial`.
- [[F-007 OneDrive locks the virtual environment]] — local `uv sync` can fail; workaround documented.
- Browser-level E2E tests not automated; Docker not installed locally (CI builds images).

## Next
1. Phase 5: technical-recession labels (H = 2, 4) from stored real GDP with censoring; as-of quarterly feature snapshots with release lags; prevalence baseline → logistic regression → gradient boosting; walk-forward evaluation with purge gaps; persisted model artifacts and metrics.
