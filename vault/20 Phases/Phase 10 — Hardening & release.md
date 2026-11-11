---
type: phase
phase: 10
title: Hardening & release
status: done
started: 2026-11-11
completed: 2026-11-11
tags:
  - phase
---

# Phase 10 — Hardening & release

## Goal
Full audit, E2E tests, verified containers and a truthful GitHub-ready release.

## Acceptance (abridged — full list with evidence in `docs/ROADMAP.md`)
- [x] Backend/frontend tests, lint, types, build — 283 pytest, 104 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`
- [x] E2E on desktop/mobile, keyboard, offline paths — 58 Playwright tests incl. axe ([[F-015 Accessibility violations found by the first axe run]])
- [x] `docker compose up --build` verified with PostgreSQL — in CI (Docker is not installed locally)
- [x] Security audit; truthful working / partial / not-implemented table — `docs/SECURITY.md`, README

## Delivered
- Offline, credential-free demo from a genuine snapshot ([[ADR-0022 Demo from a genuine snapshot, labelled as such]]): `data/demo/`, migration 0004, `demo-load` / `demo-export`, DEMO banner, `pnpm demo`.
- Security: credential redaction in stored provenance, body limits, API headers, production CSP, secret scanner (history, tree, bundle; written by the local model, reviewed), `.security-scan-allow` with reasons, dependency audits.
- Accessibility fixes (contrast, keyboard-reachable scroll regions, underlined in-text links, favicon).
- CI jobs: Security audit, E2E on the demo snapshot, Docker compose stack.
- Docs: `DEPLOY.md` (local-model draft, 4 corrections in review), `SECURITY.md`, README rewrite with real screenshots of all ten pages.

## Log
- 2026-11-11 — No demo existed; CLAUDE.md §4/§11 allow a genuine cached snapshot with source and date → snapshot of the 2026-11-09 sync, round trip exact (25,702 rows identical).
- 2026-11-11 — FRED connector never sends the key (public CSV); redaction added anyway as defence in depth, tested end to end.
- 2026-11-11 — Local model wrote `scripts/security_scan.py`: 13/14 tests on first try; the failing one was the lead's own test typo (17 vs the specified 16 characters).
- 2026-11-11 — Scanner on history: 3 findings, all reviewed false positives (2 fake test keys, 1 compose interpolation → rule fixed).
- 2026-11-11 — First E2E run: 26/58 failed (favicon 404, contrast, scroll regions, colour-only link, one wrong test target) → 58/58 after fixes.
- 2026-11-11 — `pip-audit` (49 Python packages) and `pnpm audit --prod` (144 web packages): no known vulnerabilities.
- 2026-11-11 — DEPLOY.md draft from the local model: CORS/rate-limit settings not actually read by compose (compose fixed), UTF-16 PowerShell redirect for `pg_dump`, `curl` alias in PowerShell, smoke prerequisites.
- 2026-11-11 — Clean clone of `75c88b5`: bootstrap 3 min 28 s, demo load 6.6 s, train 12.8 s; 283 pytest, 104 Vitest, lint, build, smoke 2883/2883 passed. README training time corrected from "a few minutes" to ~15 s.
- 2026-11-11 — CI run 43022549543 for `31ba843`: API, Web, E2E (58 Playwright on the demo snapshot) and the Docker compose stack on PostgreSQL passed on the first try; **Security audit failed** — the history/tree scan flagged the fake credentials in this phase's own redaction and scanner tests (the local pre-commit scan had not covered them). Reviewed by hand, allowlisted with reasons; history and tree scans now 0 findings.
- 2026-11-11 — CI run 43023762417 for `0dde5a0`: all five jobs green (API, Web, Security audit, E2E, Docker compose stack).
