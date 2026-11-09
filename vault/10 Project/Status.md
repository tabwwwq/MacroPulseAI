---
type: status
phase: 4
phase_name: Data coverage & real dashboards
updated: 2026-11-09
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** done (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- ✅ **Phase 2 — Production-grade UI system** done (2026-11-09). See [[Phase 02 — Production-grade UI system]].
- ✅ **Phase 3 — Economic data ingestion & metadata** done (2026-11-09): **21,094 real observations** from Eurostat, ECB and FRED. See [[Phase 03 — Economic data ingestion & metadata]].
- ⏭️ **Phase 4 — Data coverage & real dashboards** is next: plot the stored series on Overview, Country Explorer, Compare and Data Observatory. See [[Phase 04 — Data coverage & real dashboards]].
- No model is trained — the risk widgets say so and explain why.
- Knowledge base: this vault, with automatic activity logging ([[ADR-0010 Obsidian vault as project memory]]).

## Working (verified 2026-11-09)
- Data: `uv run macropulse data-sync` fetches 24 native series (Eurostat 16, ECB 1, FRED 7) with retries, quality checks and idempotent upserts ([[ADR-0013 Native-series ingestion with quality gate]]). Support levels from stored data: BE, DE, FR, NL `full`; US `partial`.
- API: health, ready, countries, sources/status, indicators/catalog, **`/api/indicators`** (derived series + provenance + quality checks); error contract; request ids; JSON logs.
- Web: URL-based context, KPI tiles and chart frames that show stored counts and latest periods, coverage matrix, offline/retry states, mobile layout without overflow.
- Checks: 121 pytest (+1 PostgreSQL in CI, +12 opt-in live tests), ruff, mypy `--strict`, ESLint, tsc, 53 Vitest, `next build`.

## Blockers & risks
- [[F-006 US October 2025 observations missing]] — real gap in US CPI and unemployment; Phase 5 needs an explicit quarterly aggregation rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector yet; reduced feature set for BE/NL.
- FRED metadata and ALFRED vintages need a server-side `FRED_API_KEY` (not configured) → US stays `partial`.
- [[F-007 OneDrive locks the virtual environment]] — local `uv sync` can fail; workaround documented.
- Docker not installed locally — `docker compose up` unverified (CI builds images).

## Next
1. Phase 4: KPI tiles with the latest value, change and provenance tooltip; Country Explorer charts from `/api/indicators`; Compare with aligned periods; Data Observatory lineage and per-series quality.
2. End-to-end smoke test over the four pages with the synced database; production build.
