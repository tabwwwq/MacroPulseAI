---
type: decision
id: ADR-0015
date: 2026-11-09
status: accepted
area: ml
tags:
  - decision
---

# ADR-0015 · Publish only what beats the baseline; add the term spread

> [!decision] Decision
> 1. The published model for a horizon is the candidate with the lowest **development** (2000–2014) Brier score **only if it beats the prevalence baseline there**; otherwise the best *baseline* is published and the selection note says so. Held-out results (2015+) are reported, stored as a `heldout_check`, and shown to users — they never change the choice.
> 2. Feature set `core-asof-v2` adds the **term spread** (10-year government yield minus 3-month rate), the one leading indicator available for every country from official sources (Eurostat `irt_lt_mcby_m` + euro-area `irt_st_m`; FRED `GS10` − `TB3MS`).

## Context
- The first run (`20261109T172254Z`, feature set v1: GDP, inflation, unemployment, policy rate) selected Logistic Regression for H=4 although it was *worse* than the prevalence baseline on development (Brier skill −0.141): the old rule only compared candidates with each other. Publishing it would have been fabricated superiority.
- Development diagnostics showed the v1 features are coincident: in 2008 (17/20 events) the mean H=4 probability was 0.12, in 2009 (0 events) 0.38. The yield curve is the standard leading indicator (Estrella & Mishkin 1998).
- Eurostat publishes the 3-month rate only for the euro area, so the short leg is shared by BE/DE/FR/NL (labelled like the ECB rate).

## Consequences
- v2 development skill: H=2 +0.099 (was +0.014), H=4 +0.032 (was −0.14 for the best candidate) — both now beat the baseline on development, so candidates are published.
- Held-out skill is negative for both ([[F-008 No model beats the base rate on held-out years]]); the API (`/api/models` → `heldout_check`) and the UI state this next to every mention of the model.
- The v1 run stays in `model_versions` as evidence; its held-out numbers were seen before v2 was defined (protocol note in F-008).

Related: [[Evaluation protocol]] · [[Phase 05 — Recession target, features & first model]]
