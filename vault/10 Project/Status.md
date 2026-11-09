---
type: status
phase: 2
phase_name: Production-grade UI system
updated: 2026-11-09
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** is done and committed (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- 🔜 **Phase 2 — Production-grade UI system** starts 2026-11-09. See [[Phase 02 — Production-grade UI system]].
- No economic observations are ingested and no model is trained — the app says so everywhere.
- Knowledge base: this Obsidian vault with automatic activity logging ([[ADR-0010 Obsidian vault as project memory]]).

## Working (verified 2026-11-08)
- FastAPI: health, ready, countries, sources/status; error contract; request ids; JSON logs.
- Next.js: design shell, all 10 routes, country switcher, sync badge, mobile drawer, offline + retry states.
- Checks: 27 pytest (+1 PostgreSQL test for CI), ruff, mypy `--strict`, ESLint, tsc, 16 Vitest, `next build`.
- Live source probe: 28 verified series across Eurostat, ECB, FRED, World Bank ([[Eurostat]], [[ECB]], [[FRED]], [[World Bank]], [[OECD]]).

## Blockers & risks
- [[F-001 HICP dataset frozen at 2025-12]] — blocks `full` support for BE/DE/FR/NL until a successor is verified.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — the CLI feature cannot be used for BE/NL.
- FRED metadata and ALFRED vintages need a server-side `FRED_API_KEY` (not configured).
- Docker is not installed locally — `docker compose up` unverified (CI builds images).

## Next
1. Phase 2: as-of selector, chart wrapper (ECharts), KPI card, stale/missing states, keyboard & a11y pass, screenshots.
2. Phase 3: Eurostat + ECB + FRED connectors, observations table, `data-sync` CLI.
