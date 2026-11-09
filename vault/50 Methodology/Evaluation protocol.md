---
type: methodology
status: implemented
implemented: 2026-11-09
tags:
  - methodology
  - ml
---

# 🧪 Evaluation protocol

> [!success] Implemented in Phase 5 (`packages/ml`, `uv run macropulse train`)
> Every number below comes from run `20261109T173231Z` on the stored official data (712 as-of rows).

## Splits
- **Expanding window, one fold per calendar year** from 2000; never random splits.
- **Horizon purge:** a training label for as-of *t* uses GDP for *t+1 … t+H*, and at the first test quarter *s* GDP is published only through *s−1*, so training needs *t + H ≤ s − 1*.
- **Pooled on time:** all countries' quarters of a year are tested together, so no country's later data informs another country's earlier test quarter.
- **Development** = out-of-sample predictions for 2000–2014; **held-out** = 2015 onwards. Hyperparameters are fixed in code; no tuning.
- Folds whose training window has fewer than 8 events (or non-events) are skipped and reported (H=2: 2000 and 2001).

## Leakage guards (tested)
- Scalers fit inside pipelines on training rows only — `test_scaler_is_fitted_on_training_rows_only`.
- As-of snapshots use only observations whose period ended at least the publication lag before the cut-off — `test_leakage_future_values_cannot_change_a_snapshot` poisons every ineligible value.
- Censored and missing labels never enter training or metrics.

## Models
1. Prevalence baseline (training event rate) and a contraction-rule baseline.
2. Logistic Regression (L2, C = 0.5, standardised).
3. HistGradientBoosting (depth 3, 200 iterations, learning rate 0.05, min leaf 20) and the same with **temporal Platt calibration** (latest 30 % of each training window behind a purge gap, only with ≥ 6 events of each class).
4. XGBoost: optional extra; recorded as *not installed*.

## Selection
The published model is the candidate with the lowest **development** Brier score, **only if it beats the prevalence baseline there**; otherwise the best baseline is published ([[ADR-0015 Publish only what beats the baseline]]). Held-out results are reported, never used to choose.

## Results (run 20261109T173231Z, feature set `core-asof-v2`)
| H | model | dev Brier (skill) | held-out Brier (skill) | dev ROC-AUC | n / events dev · held-out |
| --- | --- | --- | --- | --- | --- |
| 2 | prevalence | 0.097 (0) | 0.055 (0) | — | 260/27 · 224/13 |
| 2 | **hist_gbm** (published) | 0.087 (**+0.099**) | 0.080 (**−0.448**) | 0.69 | |
| 2 | logistic | 0.097 (−0.007) | 0.113 (−1.047) | 0.62 | |
| 4 | prevalence | 0.166 (0) | 0.119 (0) | — | 300/59 · 214/29 |
| 4 | **logistic** (published) | 0.160 (**+0.032**) | 0.209 (**−0.754**) | 0.57 | |
| 4 | hist_gbm | 0.177 (−0.071) | 0.192 (−0.612) | 0.60 | |

> [!warning] What this means
> Small skill on 2000–2014, **none on 2015–2026** → [[F-008 No model beats the base rate on held-out years]]. Accuracy would look high here only because most quarters have no recession — it is not reported as a headline for that reason.

Related: [[Technical recession target]] · [[Phase 05 — Recession target, features & first model]]
