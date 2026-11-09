---
type: phase
phase: 1
title: Foundation & design shell
status: done
started: 2026-11-08
completed: 2026-11-08
commit: 25366de
tags:
  - phase
---

# Phase 1 — Foundation & design shell

> [!verified] Done · 2026-11-08 · commit `25366de`
> Monorepo, typed API, design shell and live data-feasibility evidence — all checks green.

## Delivered
- **Monorepo**: pnpm workspace (`apps/web`, `packages/shared-types`) + uv workspace (`apps/api`, `packages/economics`), lockfiles, `.env.example`, CI, Dockerfiles, `compose.yml`. → [[ADR-0001 pnpm + uv monorepo]]
- **API**: `/api/health`, `/api/ready`, `/api/countries`, `/api/countries/{iso2}`, `/api/sources/status`; error contract `{"error": {code, message, details, request_id}}`; request ids; JSON logs; restricted CORS; Alembic migrations (SQLite ↔ PostgreSQL). → [[ADR-0006 SQLite locally, PostgreSQL in production]]
- **Honest state**: support levels computed from stored data, source freshness from ingestion runs. → [[ADR-0007 Support levels are computed, never declared]]
- **Web**: dark research-terminal design system, sidebar/topbar, country switcher, sync badge, mobile drawer, all 10 routes, loading / error-with-retry / offline / not-built states. → [[ADR-0005 Next.js proxies the API]]
- **Data feasibility**: 45 live probes → [[Eurostat]], [[ECB]], [[FRED]], [[World Bank]], [[OECD]]; findings [[F-001 HICP dataset frozen at 2025-12]], [[F-002 OECD CLI missing for Belgium and Netherlands]].
- **Agents**: Codex delegation runner + `AGENTS.md` → [[Agent workflow]].

## Verification (run, not assumed)
| Check | Result |
| --- | --- |
| pytest | 27 passed (+1 PostgreSQL test, runs in CI) |
| ruff / ruff format / mypy `--strict` | clean |
| ESLint / tsc | clean |
| Vitest | 16 passed |
| `next build` | OK, 12 routes |
| Browser | navigation, country switcher, mobile drawer (no overflow at 375 px), API offline → retry recovers |

> [!warning] Not verified
> `docker compose up` (Docker not installed locally); a clean-clone setup on another machine.

## Bugs found and fixed during verification
- Country names truncated in a 3-column grid → auto-fill grid.
- Horizontal page overflow on mobile (wide table widened grid items) → `min-w-0` on cards.
- Mobile logo rendered empty: SVG gradient id referenced from a `display:none` subtree → solid stroke.
- `pnpm setup` collides with pnpm's built-in command → renamed to `pnpm bootstrap`.

Full acceptance criteria: `docs/ROADMAP.md`. Journal: [[2026-11-08]].
