---
type: status
phase: 3
phase_name: Economic data ingestion & metadata
updated: 2026-11-09
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** done (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- ✅ **Phase 2 — Production-grade UI system** done (2026-11-09). See [[Phase 02 — Production-grade UI system]].
- ⏭️ **Phase 3 — Economic data ingestion & metadata** is next. See [[Phase 03 — Economic data ingestion & metadata]].
- No economic observations are ingested and no model is trained — every page says so and explains why.
- Knowledge base: this vault, with automatic activity logging ([[ADR-0010 Obsidian vault as project memory]]).

## Working (verified 2026-11-09)
- API: health, ready, countries, sources/status, **indicators/catalog**; error contract; request ids; JSON logs.
- Web: URL-based context (country + as-of quarter), KPI tiles, chart frames (ECharts, CSV/PNG, table view), country tabs, compare with comparability warnings, recession horizon toggle, forecast controls, coverage matrix, offline + retry states, mobile layout without overflow.
- Checks: 42 pytest (+1 PostgreSQL for CI), ruff, mypy `--strict`, ESLint, tsc, 52 Vitest, `next build`.

## Blockers & risks
- [[F-001 HICP dataset frozen at 2025-12]] — a current HICP successor must be verified in Phase 3 before any euro-area country can reach `full`.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — reduced feature set for BE/NL.
- FRED metadata and ALFRED vintages need a server-side `FRED_API_KEY` (not configured).
- Docker not installed locally — `docker compose up` unverified (CI builds images).

## Next
1. Phase 3: `observations` table + migration; Eurostat (GDP, unemployment, debt) and ECB connectors with retries, provenance and quality checks; `macropulse data-sync` CLI; real ingestion runs feeding source health.
2. Find and verify the HICP successor dataset; decide FRED (CSV vs API key) for the US.
