# AGENTS.md — MacroPulse AI (instructions for Codex and other coding agents)

The authoritative product and engineering specification is [`CLAUDE.md`](CLAUDE.md); the phase plan is
[`MACROPULSE_PHASE_PROMPTS.md`](MACROPULSE_PHASE_PROMPTS.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).
Read the relevant parts before changing code. This file only adds agent-collaboration rules.

## Roles

- **Claude Code is the lead engineer.** It owns architecture, the task list and final verification.
- **Codex is a delegated side-task engineer.** It receives scoped briefs via
  `scripts/agents/codex-task.ps1` (or directly from the user) and must stay inside the brief's scope.
- Two agents never edit the same file at the same time. If a brief lists files/directories, touch only
  those. If you need to change something else, stop and say so in your final report.

## Non-negotiable rules (from CLAUDE.md)

- Never fabricate economic data, model metrics, predictions, API responses or test results.
- Never claim something works without running it. Report commands you ran and their real output.
- Missing data stays missing (`null`/`N/A` + reason). No silent imputation of official series.
- No secrets in code, fixtures, logs or client bundles. Server-side `FRED_API_KEY` only.
- Time-series ML: no random splits, no fitting scalers/imputers on future data, censor unobservable labels.
- Technical recession (2 consecutive negative q/q real GDP quarters) is **not** an NBER recession; keep them separate.
- Do not commit, push, rebase, switch branches or delete files you did not create unless the brief says so.

## Repository layout

```
apps/web          Next.js App Router + TypeScript (strict) + Tailwind + TanStack Query + ECharts
apps/api          FastAPI service (Python 3.12, Pydantic v2, SQLAlchemy 2, Alembic)
packages/economics  data connectors, transforms, quality checks (Python)
packages/ml         labeling, features, training, evaluation, inference (Python)
packages/shared-types  TypeScript types generated from the FastAPI OpenAPI schema
docs/             architecture, data feasibility, methodology, roadmap
scripts/          dev/test helpers (PowerShell-first), scripts/agents for agent delegation
data/demo         small, attributed, clearly labelled DEMO fixtures only
```

## Commands (Windows PowerShell; POSIX equivalents in README)

```powershell
pnpm install                 # JS deps (workspace)
uv sync --all-packages       # Python deps (uv workspace, Python 3.12)
pnpm dev                     # API (:8000) + web (:3000)
pnpm test                    # pytest + vitest
pnpm lint                    # ruff + mypy + eslint + tsc
pnpm build                   # Next.js production build
pnpm gen:types               # regenerate packages/shared-types from FastAPI OpenAPI
```

Run the narrowest relevant checks for what you changed and include the results in your report.

## Style

- Python: ruff (lint+format), type hints everywhere, mypy-clean where practical, pytest with tiny
  deterministic local fixtures; live-API tests are marked `@pytest.mark.live` and skipped by default.
- TypeScript: strict mode, no `any` without a comment, components small and accessible
  (keyboard + screen reader), design tokens from `apps/web/src/styles`, never hard-coded colours.
- UI: never render a control that does nothing; unbuilt features are disabled or omitted with a clear label.

## Final report format (for delegated tasks)

1. Summary (2–4 lines) 2. Files changed 3. Commands run → result 4. Unverified / open questions.
