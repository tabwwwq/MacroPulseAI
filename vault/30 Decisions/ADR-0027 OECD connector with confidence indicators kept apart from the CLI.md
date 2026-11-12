---
type: decision
id: ADR-0027
date: 2026-11-12
status: accepted
area: data
tags:
  - decision
---

# ADR-0027 · OECD connector, with confidence indicators kept apart from the CLI

> [!decision] Decision
> A fourth connector reads the OECD SDMX REST API (`sdmx.oecd.org/public/rest/data`, CSV output) for the *Composite leading indicators* dataflow `OECD.SDD.STES,DSD_STES@DF_CLI,4.1`, with fully specified keys `{ISO3}.M.{MEASURE}.IX._Z.AA.IX._Z.H` (monthly, index, amplitude adjusted, OECD harmonised). It syncs the composite leading indicator (`LI`) for DE, FR and US, and two **new indicators** for all five countries: composite business confidence (`BCICP`) and composite consumer confidence (`CCICP`).

## Why
- The CLI was registered since Phase 1 but never synced ("3/5 sources synced"). Keys and parsing were verified against the live API before any mapping was changed (CLAUDE.md §4).
- Belgium and the Netherlands have no CLI ([[F-002 OECD CLI missing for Belgium and Netherlands]]). Their confidence indices are real, comparable OECD series, so they become indicators of their own instead of a relabelled CLI.
- Every dimension of the key is fixed: a partial key returns 16–17 series for DE, FR and US (normalised, trend-restored, growth rates, components), and the parser rejects any row whose key differs, any unit multiplier other than 0 and any duplicate period.
- The dataflow version is pinned (4.1); an unknown dataflow is an error, never a guess.

## Consequences
- The indicators appear on the country page (Growth tab, *leading* category) with provenance, and in the data observatory; the models do not use them (`EXCLUDED_INPUTS`: not in the pre-registered feature set).
- The OECD CLI is revised after release and has no stored vintages; adding it to the models would need the same release-lag care as every other input.
- The demo snapshot (2026-11-09) has no OECD rows; in demo mode these indicators show as not synced.
- The local model wrote the connector from specification tests ([[ADR-0021 Local model as a reviewed single-file worker]]).
