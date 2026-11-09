---
type: phase
phase: 4
title: Data coverage & real dashboards
status: done
started: 2026-11-09
completed: 2026-11-09
tags:
  - phase
---

# Phase 4 — Data coverage & real dashboards

## Goal
Make Overview, Country Explorer, Compare and Data Observatory useful with stored official data.

## Acceptance (abridged — full list in `docs/ROADMAP.md`)
- [x] Provenance on every KPI and chart (source, unit, adjustment, period, retrieval time; per-observation publication dates are not offered by the APIs)
- [x] Country/date selection changes data; comparisons of up to four countries
- [x] Coverage matrix, freshness vs observation age, CSV export with citations
- [x] Support levels computed from validated coverage (BE/DE/FR/NL `full`, US `partial`)

## What was built
- **API:** `/api/countries/{iso2}/summary?as_of=` (latest value, change, source flag, staleness, provenance; as-of cut-off), `/api/countries/{iso2}/data-quality` and `/api/data-quality` (per-series lineage + latest checks), `/api/observations/export` (raw rows with per-row provenance). One shared loader `services/series_data.py` feeds charts, KPIs and lineage.
- **Web:** KPI tiles with change, flags (provisional / estimated) and a keyboard-reachable provenance tooltip; `IndicatorChart` (hover source, quality notes, request link, NBER reference bands for the US, step lines for ECB decisions); history window `?range=`; Compare with as-published or spread-vs-baseline modes; Data Observatory inventory with source filter and CSV links.
- **Checks:** `scripts/smoke_api.py` (`pnpm smoke`) — end-to-end API invariants over the stored data.
- Decision: [[ADR-0014 As-of cut-off over revised data]].

## Verified (2026-11-09)
136 pytest · 70 Vitest · ruff / mypy `--strict` / ESLint / tsc clean · `next build` · `pnpm smoke` 348/348 · four pages in the browser for every country at 1440 px and 375 px (no horizontal overflow) · as-of check: US 2008-Q4 real GDP q/q −2.19 %, unemployment 7.3 %.

> [!warning] Not automated
> Browser-level end-to-end tests do not exist yet; the page checks were done by hand. The API side is automated by `pnpm smoke`.

## Log
- 2026-11-09 — Phase 3 pushed to GitHub (`90e0e91`); GitHub Actions CI green.
- 2026-11-09 — Summary, data-quality and CSV endpoints + 15 API tests on real fixtures.
- 2026-11-09 — Dashboards wired; found and fixed: page scroll captured by chart zoom (now Ctrl + wheel), SDMX status `A` ("normal") counted as a source flag (quality rule fixed, data re-synced as runs 7–9), dense charts drawing thousands of markers.
- 2026-11-09 — Chart CSV exports now carry each series' citation in the header.
