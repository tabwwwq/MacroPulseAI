---
type: decision
id: ADR-0016
date: 2026-11-09
status: accepted
area: ml
tags:
  - decision
---

# ADR-0016 · Inference serving and explanations

> [!decision] Decision
> Probabilities are computed **on request** from stored observations and the saved artifact of the published model (no cached numbers), and every response carries the context needed to judge it: version, as-of and cut-off, freshness, explanation, measured track record, and an **in-sample** flag with the walk-forward estimate for historical as-of quarters.

## Details
- **Trust boundary:** artifacts are joblib pickles, so the API only loads files inside `MODELS_DIR` (`model_artifact_untrusted` otherwise) and refuses missing files or a different feature set with actionable 503s.
- **Explanations without SHAP** (not installed): for the logistic pipeline, standardised coefficient × standardised value — exact and additive in log-odds with the intercept; for tree models, a local sensitivity (probability minus probability with one input at its training mean), documented as non-additive. Inputs outside the training range or the 5th–95th percentile are flagged.
- **Bands** are fixed in advance: low < 15 %, moderate < 30 %, elevated < 50 %, high ≥ 50 %, always written out in text; the training base rate is shown next to the number.
- **No interval:** with 13–29 held-out events an interval would mostly reflect sampling noise; the track record is the uncertainty statement, and this is said in the limitations.
- **History** shows only walk-forward predictions (each fold model trained on outcomes known before that year), the prevalence baseline from the same folds, and the current estimate as a separate series.
- **Horizon consistency:** when P(4Q) < P(2Q) the UI says the two separate models contradict each other instead of adjusting either number ([[F-009 Separate horizon models can contradict each other]]).

## Consequences
The round trip is testable (recomputed = stored at training) and checked by `pnpm smoke`. A user can see when a number is a fit rather than a forecast, and how often this kind of model was wrong.

Related: [[ADR-0015 Publish only what beats the baseline]] · [[Phase 06 — Explainable risk dashboard & ML lab]]
