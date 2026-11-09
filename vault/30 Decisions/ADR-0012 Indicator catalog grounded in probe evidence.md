---
type: decision
id: ADR-0012
date: 2026-11-09
status: accepted
area: data
tags:
  - decision
---

# ADR-0012 · Indicator catalog grounded in probe evidence

> [!decision] Decision
> `packages/economics/indicators.py` defines 9 indicators and, per country, the exact source dataset/key plus the status the live probe observed (verified, partial, stale, not published, unmapped). `GET /api/indicators/catalog` serves it together with the stored-observation count.

## Context
Before observations exist, the UI still has to say *what* each tile will show, *where* it comes from and *why* it is empty — without inventing values. The probe ([[Eurostat]], [[ECB]], [[FRED]], [[World Bank]], [[OECD]]) already established those facts.

## Consequences
- KPI tiles, chart frames, the compare page and the coverage matrix explain emptiness precisely (e.g. [[F-001 HICP dataset frozen at 2025-12]], [[F-002 OECD CLI missing for Belgium and Netherlands]]).
- Comparability warnings are computed (different datasets, federal vs general-government debt, shared ECB rate).
- Phase 3 connectors consume the same mappings, so code and documentation cannot drift; tests pin the probe findings.
