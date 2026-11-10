---
type: phase
phase: 8
title: Crisis time machine
status: done
started: 2026-11-10
completed: 2026-11-10
tags:
  - phase
---

# Phase 8 — Crisis time machine

## Goal
Historic as-of replay with strict temporal eligibility.

## Acceptance (abridged — full list with evidence in `docs/ROADMAP.md`)
- [x] ALFRED vintages for the US when verified — **not verified** (`FRED_API_KEY` not configured), so not claimed; US replays are approximations too
- [x] 'Revised-data / release-lag approximation' label — banner, badge and API `basis` with the lag table
- [x] Predicted risk vs subsequently observed outcome, including misses — verdict per replay, warned / missed / false alarms per country ([[F-013 Replays show most recessions were missed]])
- [x] Temporal-leakage tests — future deleted ⇒ identical estimates; purge mutation detected

## Delivered
- `services/replay.py`; `GET /api/history/replay`, `/api/history/episodes`, `/api/history/presets` ([[ADR-0019 Replays are walk-forward fold estimates]]).
- Web `/history`: basis banner, horizon, crisis presets, quarter scrubber, walk-forward estimate with fold and verdict, inputs known at the cut-off, outcome window, NBER box (US), GDP bars, walk-forward timeline with recession bands and replay marker, episodes with one-click replay.
- `ChartSeries.color` for series whose palette colour would imply a meaning.

## Verified
234 pytest · 97 Vitest · ruff/mypy `--strict`/ESLint/tsc · `next build` · `pnpm smoke` 2818/2818 (40 crisis replays) · browser: presets, scrubber, horizon switch, episode links, 404 state, 375 px.

## Log
- 2026-11-10 — Confirmed the fold rule: training as-of t with t + H ≤ Y-Q1 − 1; that GDP is published by the end of Y-Q1.
- 2026-11-10 — Leakage test: deleting all data published after 2008-Q2 reproduces every model's estimate exactly (both horizons); removing the purge is caught.
- 2026-11-10 — `FRED_API_KEY` not configured → no ALFRED; replays labelled approximations everywhere.
- 2026-11-10 — Real-data tally: 2Q warned 0 / 20, 4Q 6 / 22, 26 false-alarm episodes → [[F-013 Replays show most recessions were missed]].
- 2026-11-10 — UI fixes after screenshots: full-width scrubber, one-quarter replay marker, neutral colour for "published later", scroll to the result after an episode link.
