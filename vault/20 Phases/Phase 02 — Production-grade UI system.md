---
type: phase
phase: 2
title: Production-grade UI system
status: done
started: 2026-11-09
completed: 2026-11-09
tags:
  - phase
---

# Phase 2 — Production-grade UI system

> [!verified] Done · 2026-11-09
> Every page has a real layout wired to typed API queries, honest empty/stale/error states, working selectors and controls — and still not a single invented number.

## Delivered
- **Global analysis context in the URL** — country + as-of quarter (`?country=DE&asOf=2008-Q3`) survive navigation and are shareable → [[ADR-0011 Analysis context lives in the URL]].
- **As-of selector** (1995-Q1 … current quarter, grouped by year), **country switcher** that follows the context, compact mobile topbar.
- **Indicator catalog API** `GET /api/indicators/catalog` — 9 indicators × 5 countries with source dataset/key and the live-probe status (verified / partial / stale / not published / unmapped) → [[ADR-0012 Indicator catalog grounded in probe evidence]].
- **Design-system components:** `KpiCard`, `KpiGrid`, `ChartFrame` + `TimeSeriesChart` (ECharts, modular, CSV/PNG export, accessible table view — built by Codex: [[2026-11-09 1201 chart-frame]]), `Segmented` radio group, `WidgetBoundary` error boundary, `CoverageMatrix`.
- **Pages:** Overview (guided country choice → 6 KPI tiles, risk timeline, coverage, charts), Country explorer (7 tabs in the URL, per-indicator chart frames, source table), Compare (≤4 countries, comparability warnings e.g. HICP vs CPI), Recession risk (2Q/4Q horizon, explicit "Model not trained"), Forecast studio (indicator + horizon), Data observatory (coverage matrix).

## Verification (run, not assumed)
| Check | Result |
| --- | --- |
| pytest | 42 passed (+1 PostgreSQL test for CI) |
| ruff / format / mypy `--strict` | clean |
| ESLint / tsc | clean |
| Vitest | 52 passed in 11 files |
| `next build` | OK, 12 routes |
| Browser | guided selection → `?country=DE`; as-of → `&asOf=2008-Q3`; context kept through the mobile drawer; horizon toggle → `&h=4`; compare chips + metric; tabs by keyboard (arrows → `?tab=prices`) |
| Mobile 375 px | no horizontal overflow on `/`, `/countries/*`, `/compare`, `/recession`, `/forecasts`, `/data`, `/lab` |

## Bugs found and fixed during verification
- `/data` was 714 px wide on mobile: `sr-only` text inside table cells is absolutely positioned and escaped an *unpositioned* `overflow-x-auto` container → all scroll containers are now `relative`.
- `/compare` overflowed by 10 px: the 5-option segmented control could not wrap → `flex-wrap`.
- Stale-HICP reason repeated itself → the finding note is used verbatim.
- Chart footer said "retrieved —" before any fetch → "not retrieved yet".

## Log
- 2026-11-09 — Phase started; Codex delegated the chart layer; catalog API + context + pages built; verified and committed.
