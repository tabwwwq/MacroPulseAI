---
type: reference
tags:
  - project
aliases:
  - Principles
---

# 🎯 Vision & principles

**MacroPulse AI** lets analysts, consultants and students monitor the economic health of Belgium, Germany, France, the Netherlands and the United States, explore official macro series, and inspect a transparent, calibrated estimate of the probability of a *technical recession* in the next 2 and 4 quarters. Specification: `CLAUDE.md` (authoritative) and `MACROPULSE_PHASE_PROMPTS.md`.

## Non-negotiables
- **No fabricated data, metrics or predictions.** Every number traces to a sourced observation or a measured model output.
- **Missing stays missing** — `null` / N/A with a reason; no silent imputation of official series.
- **Honest UI** — unbuilt features are disabled or labelled "not built yet"; no fake controls, no false "Live" badges.
- **Technical recession ≠ NBER recession** — see [[Technical recession target]].
- **No leakage** — walk-forward evaluation, horizon gaps, train-only preprocessing — see [[Evaluation protocol]].
- **Verify before claiming** — nothing is reported as working without being run.

## What the UI must always distinguish
1. Historical statistics
2. Latest published data
3. Trained model predictions
4. Exploratory sensitivity simulations (non-causal)
5. Demo / sample data

## Definition of done (short)
Clone → documented setup → responsive app on all completed pages → real sourced data with provenance → one reproducible training/backtest with honest metrics (or an explicit untrained state) → downloadable report → tests and production build pass. See [[Phase 10 — Hardening & release]].
