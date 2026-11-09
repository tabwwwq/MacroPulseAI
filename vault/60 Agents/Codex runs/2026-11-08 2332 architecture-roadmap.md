---
type: codex-run
name: architecture-roadmap
date: 2026-11-08
time: "23:32"
status: success
exit_code: 0
sandbox: workspace-write
network: false
tags:
  - agent/codex
---

# ✅ Codex · architecture-roadmap

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-08 23:32. Sandbox `workspace-write`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> 1. **Summary:** Created architecture and roadmap docs that distinguish implemented behavior, lead-reported verification, planned work, and data blockers.
>
> 2. **Files changed:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/ROADMAP.md](docs/ROADMAP.md). Only these files were created.
>
> 3. **Commands run → result:** PowerShell document checks passed: local links resolve, code fences balance, all 9 architecture sections and 10 phases exist, and checked criteria appear only in Phase 1. `rg` and `git` were unavailable; used PowerShell for inspection.
>
> 4. **Unverified:** Application checks were not rerun; Phase 1 results are attributed to the lead engineer. Mermaid rendering and Docker execution remain unverified.

> [!quote]- Brief sent to Codex
> You are Codex, a delegated side-task engineer on the MacroPulse AI repository.
> Read AGENTS.md first and follow it; CLAUDE.md is the authoritative specification.
> Stay strictly inside the scope of the task below and touch only the files it allows.
> Do not commit, push, switch branches, or delete files you did not create.
> Never fabricate data, API responses, metrics or test results; mark anything you could not verify.
> End with the report format from AGENTS.md (summary, files changed, commands run -> result, unverified).
>
> --- TASK: architecture-roadmap ---
> # Brief: write docs/ARCHITECTURE.md and docs/ROADMAP.md
>
> ## Files you may create (and nothing else)
> - `docs/ARCHITECTURE.md`
> - `docs/ROADMAP.md`
>
> The lead engineer is editing README.md, compose.yml, Dockerfiles and .github/ at the same time — do not
> touch them. Read whatever you need: CLAUDE.md, MACROPULSE_PHASE_PROMPTS.md, AGENTS.md,
> docs/DATA_FEASIBILITY.md, apps/api/**, packages/**, apps/web/src/**, package.json, pyproject.toml.
>
> ## Ground truth you cannot see in the code (state these as decisions)
> - Phase 1 is implemented and verified locally on Windows 11 (2026-11-08): 27 pytest tests, ruff, ruff format,
>   mypy --strict clean; web: tsc clean, ESLint clean, 16 vitest tests, `next build` OK (12 routes);
>   manual browser check of navigation, country switcher, mobile drawer, API-offline + retry states.
> - Python 3.12 via uv workspace (`apps/api`, `packages/economics`); `.python-version` = 3.12. Python 3.15 is
>   installed on the machine but is too new for the scientific stack.
> - TypeScript pinned to 6.0.3 (not 7.x): the native TS 7 compiler is not yet compatible with Next.js
>   type-checking and openapi-typescript. ESLint pinned to 9.39.5 because eslint-config-next's plugins
>   (react, jsx-a11y, import) do not support ESLint 10 yet.
> - The browser never calls FastAPI directly: Next.js rewrites `/api/*` to `API_URL` server-side
>   (apps/web/next.config.ts). CORS on FastAPI is still restricted to explicit origins.
> - Local dev uses SQLite (`data/local/macropulse.db`); PostgreSQL is the production target via compose.
>   Migrations are written portably (naming convention, batch mode on SQLite). Docker is NOT installed on
>   the dev machine, so compose/Docker images are written but unverified locally (CI will build them).
> - Python on Windows needs the certifi CA bundle for Eurostat/ECB TLS (system store lacks on-demand roots);
>   connectors will use httpx (certifi by default).
> - Codex (you) is used for delegated side tasks via scripts/agents/codex-task.ps1; its Windows sandbox has
>   no network and no per-user Python, so live probes are run by the lead engineer.
>
> ## docs/ARCHITECTURE.md — required sections (concise, tables and diagrams over prose)
> 1. System context + container diagram (Mermaid `flowchart`): browser → Next.js (App Router, proxy) →
>    FastAPI → SQLite/PostgreSQL; offline jobs (data sync, training) planned; official sources.
> 2. Repository layout table (what lives where, with real paths).
> 3. Request lifecycle: request id middleware, structured JSON logs, error contract
>    (`{"error": {code, message, details, request_id}}`), 422 for invalid/unsupported country, 503 for
>    unmigrated DB (`database_unavailable`), readiness probe semantics.
> 4. Data model: implemented tables (countries, data_sources, ingestion_runs) and planned entities from
>    CLAUDE.md §5 with the phase in which each lands. Mark planned clearly.
> 5. Typed contract: Pydantic → OpenAPI → `packages/shared-types` (openapi-typescript) → openapi-fetch +
>    TanStack Query; regeneration command.
> 6. Frontend architecture: module registry (`apps/web/src/lib/modules.ts`) as the single source of truth for
>    navigation/phase state, design tokens in globals.css, honest states (loading/error/empty/not-built).
> 7. Planned data & ML pipeline (from CLAUDE.md §4–6): connectors → normalised observations with provenance →
>    quality checks → as-of quarterly feature snapshots with release-lag assumptions → labels (technical
>    recession within H=2/4, censoring) → walk-forward training/evaluation → versioned artifacts → inference.
>    Mark everything here as PLANNED.
> 8. Security & reliability model (what exists now vs planned).
> 9. Decision log (short ADR table): the decisions above plus any you can justify from the code.
>
> ## docs/ROADMAP.md — required content
> - One section per phase 1–10 (names from CLAUDE.md §12 build order and MACROPULSE_PHASE_PROMPTS.md):
>   goal, deliverables, **explicit, testable acceptance criteria** (checkboxes), and status.
> - Phase 1 checkboxes ticked only for what is listed as verified above; everything else unticked.
> - Include the per-country support targets and the data blockers from docs/DATA_FEASIBILITY.md that gate
>   `full` support (stale HICP dataset, BE/NL missing OECD CLI, FRED metadata/ALFRED need API key).
> - A short "Definition of done" section mirroring CLAUDE.md.
>
> No marketing language; never claim unbuilt features work.
