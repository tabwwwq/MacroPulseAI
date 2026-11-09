---
type: finding
id: F-007
severity: low
status: open
area: tooling
found: 2026-11-09
tags:
  - finding
---

# F-007 · OneDrive locks the virtual environment

> [!finding] Low severity · open (local tooling)
> The repository lives in a OneDrive folder. `uv sync --all-packages` failed with `Access is denied (os error 5)` while removing `.venv/Lib/site-packages/macropulse_*-0.1.0.dist-info`. Both folders had become empty OneDrive placeholders (attributes `ReadOnly, ReparsePoint`); no process held them.

## Impact
A dependency sync can fail half-way and leave the `macropulse` entry point missing until it is re-run.

## Action
Workaround used: `attrib -r` + `rmdir` on the two empty placeholder folders, then `uv sync` succeeded. Durable options: mark `.venv` and `node_modules` as "Always keep on this device" or exclude them from OneDrive, or point `UV_PROJECT_ENVIRONMENT` at a folder outside OneDrive.

Related: [[ADR-0001 pnpm + uv monorepo]]
