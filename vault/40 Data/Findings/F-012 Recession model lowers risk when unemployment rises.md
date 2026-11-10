---
type: finding
id: F-012
severity: medium
status: open
area: ml
found: 2026-11-10
tags:
  - finding
---

# F-012 · Recession model lowers risk when unemployment rises

> [!finding] Medium severity · open
> In the scenario lab, an unemployment shock of **+2 pp lowers** the published 4-quarter estimate (Logistic Regression, run `20261110T142434Z`) in every country: BE 24.8 → 21.3 %, DE 18.3 → 15.5 %, FR 14.2 → 11.9 %, NL 14.9 → 12.5 %, US 16.7 → 14.1 %. The six-month change in unemployment contributes −0.268 log-odds and the level +0.065. The 2-quarter HistGradientBoosting model mostly raises the estimate (BE 4.4 → 7.4 %, US 1.4 → 4.1 %; FR 20.9 → 19.5 % is the exception).

## Interpretation (hypothesis, not tested)
Unemployment lags output. In the training panel a sharp rise in unemployment tends to come during or right after a technical recession, when the *next* four quarters are often recovery, so the pooled linear model learns a negative weight on the recent change. The model answers its own question — a recession starting within the window — not "is the labour market a warning sign?".

## Impact
A reader could take the scenario as evidence that higher unemployment is good news. The disclaimer (sensitivity, not causation) covers it, but the effect is surprising enough to state.

## Action
Recorded here and kept visible in the lab (the contribution deltas show which input drives it); nothing is tuned to make the response look intuitive. To revisit with the model work in Phase 10: test on development years whether excluding `unemp_chg_6m`, or conditioning on the current GDP state, changes development Brier skill.

Related: [[ADR-0018 Scenario lab as bounded model sensitivity]] · [[F-008 No model beats the base rate on held-out years]]
