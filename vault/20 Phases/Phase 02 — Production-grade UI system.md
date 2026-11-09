---
type: phase
phase: 2
title: Production-grade UI system
status: in-progress
started: 2026-11-09
completed:
tags:
  - phase
---

# Phase 2 — Production-grade UI system

> [!phase] In progress · started 2026-11-09

## Goal
A refined, responsive design system where every page layout exists with strictly empty/unavailable states wired to typed API queries — no fake numbers — and every control works.

## Scope
- Sidebar, topbar, country selector, **as-of selector**, chart wrappers, KPI cards
- Missing-data and **stale-data** states, loading skeletons, error boundaries, tooltips, mobile menus
- Keyboard navigation and screen-reader names; reduced motion; responsive desktop/tablet/mobile
- Screenshots of every page; fix overflow and broken interactions

## Acceptance (abridged — full list in `docs/ROADMAP.md`)
- [ ] All module layouts use shared tokens/components and typed queries
- [ ] Keyboard traversal and focus handling work for shell, selectors, tooltips, mobile menu
- [ ] Country/as-of selectors and every enabled control visibly change state
- [ ] Loading, empty, stale, API-error and retry states exercised with deterministic tests
- [ ] Desktop/tablet/mobile inspected for overflow; screenshots recorded
- [ ] Frontend tests, lint/type checks and production build pass

## Log
Progress notes are appended here as the phase advances.
