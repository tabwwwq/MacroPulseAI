---
type: finding
id: F-009
severity: medium
status: open
area: ml
found: 2026-11-09
tags:
  - finding
---

# F-009 · Separate horizon models can contradict each other

> [!finding] Medium severity · open
> For France as of 2026-Q3 the published models give **20.9 % for the next 2 quarters** but **14.2 % for the next 4 quarters** (run `20261109T182857Z`). A technical recession inside *t+1…t+2* is also inside *t+1…t+4*, so P(4Q) ≥ P(2Q) must hold. The two horizons are trained as separate models (HistGradientBoosting for 2Q, Logistic Regression for 4Q) and nothing enforces the ordering.

## Impact
Users could read the pair as "risk falls later", which the definition does not allow. Both numbers are rough in any case (see [[F-008 No model beats the base rate on held-out years]]).

## Action
Done now: the Overview risk card and the Recession risk page state the contradiction whenever P(4Q) < P(2Q) — no number is silently adjusted. Later, to be decided on development data: a joint model (e.g. predicting the 2Q and the 3–4Q windows and combining them), or reporting the 4Q estimate as max(P2, P4) with that rule documented.

Related: [[ADR-0016 Inference serving and explanations]]
