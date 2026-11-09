---
type: decision
id: ADR-0007
date: 2026-11-08
status: accepted
area: product
tags:
  - decision
---

# ADR-0007 · Support levels are computed, never declared

> [!decision] Decision
> The registry stores only a *target* level; the API computes the *current* level from stored observations (`unavailable` until data is ingested). Source freshness is derived from recorded ingestion runs.

## Context
Advertising a country as fully supported before its data exists would be a false claim.

## Consequences
The UI shows 'No data yet' and 'Never synced' today — truthfully.
