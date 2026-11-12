---
type: finding
id: F-019
severity: medium
status: open
area: ml
found: 2026-11-12
tags:
  - finding
---

# F-019 · The neural network wins H=4 by a small margin and reacts strongly to inflation acceleration

> [!finding] Medium · open
> Run `20261112T150103Z` and a seed study on the same walk-forward folds (the study decides nothing; selection is unchanged).

## Evidence
- Development Brier H=4: MLP 0.1582 vs logistic 0.1600, a margin of 0.002. Seeds 1, 2, 3, 7, 42, 123 give 0.1577–0.1599; every seed beats logistic (0.1603 in the study), so the choice is not a seed accident.
- Held-out Brier H=4 across the same seeds: **0.165–0.204** (prevalence 0.119). The fitted function varies with the initialisation; no seed beats the base rate.
- Current estimates (as-of 2026-Q3), MLP vs the previous logistic model: BE **50.2 %** vs 24.8 %, DE 20.6 % vs 18.3 %, FR 17.5 % vs 14.2 %, NL 7.8 % vs 14.9 %, US 18.4 % vs 16.7 %.
- Belgium: the 6-month change in inflation, +2.8 pp, is above the training 95th percentile (2.24, z = 2.0). It is the largest contributor (+0.39 of probability) and is labelled *unusual (outside 5–95 %)* on the recession page.

## Impact
A pre-registered rule picked a model whose held-out skill is negative and whose response to an unusual input is much steeper than the linear model's. The number is shown with its caveats; it must not be read as "Belgium is in a coin-flip recession".

## Action
Keep the rule: changing it after seeing held-out results would be post-hoc selection. Candidates for a future, pre-registered change: averaging several seeds (variance), monotonic constraints (see [[F-012 Recession model lowers risk when unemployment rises]]).

Related: [[ADR-0026 Small neural network as a walk-forward candidate]], [[F-008 No model beats the base rate on held-out years]], [[F-009 Separate horizon models can contradict each other]]
