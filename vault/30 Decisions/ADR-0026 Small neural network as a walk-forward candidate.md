---
type: decision
id: ADR-0026
date: 2026-11-12
status: accepted
area: ml
tags:
  - decision
---

# ADR-0026 · A small neural network as one more walk-forward candidate

> [!decision] Decision
> `mlp` joins the candidates: standardised features → one hidden layer of 8 tanh units → logistic output, L2 `alpha = 3.0`, full-batch L-BFGS, seed from the run. Hyperparameters were fixed before the first backtest and are not tuned. It goes through the same walk-forward folds and the same selection rule as every model (lowest **development** Brier, only if it beats prevalence; held-out never consulted).

## Why
- CLAUDE.md §6 allows a neural model only as an honestly evaluated comparison. A pooled panel of ~700 labelled quarters with ~100 events cannot support an LSTM; a tiny, heavily regularised MLP is the smallest network that can represent interactions the logistic model cannot, and scikit-learn already ships it (no PyTorch dependency).
- The pipeline step is named `net`, not `model`, so explanations use the documented local sensitivity instead of linear coefficients.

## Result (run `20261112T150103Z`)
- H=4: published by the rule — development Brier 0.1582 vs logistic 0.1600 and prevalence 0.1656. Held-out 2015+: 0.183 vs prevalence 0.119, Brier skill **−0.531** (logistic was −0.754). It still does **not** beat the base rate ([[F-008 No model beats the base rate on held-out years]]).
- H=2: HistGradientBoosting stays published (MLP 0.094 vs 0.087 on development).
- Caveats: [[F-019 The neural network wins H=4 by a small margin and reacts strongly to inflation acceleration]].
