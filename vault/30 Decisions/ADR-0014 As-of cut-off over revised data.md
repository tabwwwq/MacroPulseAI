---
type: decision
id: ADR-0014
date: 2026-11-09
status: accepted
area: data
tags:
  - decision
---

# ADR-0014 · As-of cut-off over revised data

> [!decision] Decision
> The dashboards' as-of quarter is a **reference-period cut-off** applied server-side: values for periods ending on or before the end of that quarter (or today, if earlier), taken from the **latest stored revision**. Every response with an as-of says so (`data_basis`), and the UI shows a "Revised data, not vintages" badge.

## Context
- The stored series are latest revisions; Eurostat, ECB and the FRED graph endpoint give no vintages and no per-observation publication dates ([[ADR-0013 Native-series ingestion with quality gate]]).
- Users still need to look at "what the data looked like around 2008" for context, while the spec forbids implying point-in-time knowledge.
- Release lags are a modelling concern (Phase 5); applying guessed lags in the dashboards would be a silent assumption.

## Consequences
- `GET /api/countries/{iso2}/summary?as_of=` and chart `end` bounds use the same cut-off; a future quarter is rejected with 422.
- Staleness is measured at the cut-off (days since the period ended), separately from fetch freshness.
- No publication lag is applied here; Phase 5 features must apply conservative release lags, and Phase 8 replays stay labelled *revised-data / release-lag approximation* until vintage sources (ALFRED, `prc_hicp_fpd`) exist.
- Comparisons in spread mode use only periods both countries published and are refused for mixed native frequencies.
