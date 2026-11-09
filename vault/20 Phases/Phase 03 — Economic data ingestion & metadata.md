---
type: phase
phase: 3
title: Economic data ingestion & metadata
status: next
started:
completed:
tags:
  - phase
---

# Phase 3 — Economic data ingestion & metadata

## Goal
Retrieve and store genuine official observations with provenance, quality checks and a `data-sync` CLI.

## Acceptance (abridged — full list in `docs/ROADMAP.md`)
- [ ] Live-verified Eurostat GDP + another Eurostat indicator; ECB and FRED as practical
- [ ] Observations store unit, frequency, seasonal adjustment, period, retrieval and publication/vintage dates
- [ ] Retries, rate limits, resumable idempotent upserts, partial-failure handling
- [ ] Source-health API backed by real ingestion runs; real row counts reported

## Dependencies & notes
[[F-001 HICP dataset frozen at 2025-12]] must be resolved; reuse verified keys from [[Eurostat]], [[ECB]], [[FRED]].
