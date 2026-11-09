---
type: finding
id: F-008
severity: high
status: open
area: ml
found: 2026-11-09
tags:
  - finding
---

# F-008 · No model beats the base rate on held-out years

> [!finding] High severity · open
> Run `20261109T173231Z` (feature set `core-asof-v2`): every candidate model has **negative Brier skill against the prevalence baseline on the held-out years 2015–2026** — published H=2 HistGradientBoosting −0.448 (13 events in 224 rows), published H=4 Logistic Regression −0.754 (29 events in 214 rows) — although both beat the baseline on the 2000–2014 development backtest (+0.099, +0.032).

## Evidence (held-out predictions by year, H=4 logistic, mean probability / events)
- **2019 → 2020:** mean probabilities 0.10–0.29 for the as-of quarters of 2019, which carry 17 of the 29 held-out events — their windows contain the 2019-Q4/2020-H1 contraction, mostly the COVID shock, which macro inputs could not show in advance.
- **2020–2021:** 0.30–0.69 with no events — the model reacts to the collapse after it happened.
- **2022:** DE 0.75 / NL 0.84 with events (correct), BE 0.70 / US 0.54 / FR 0.45 without (false alarms; curve inversion and rate hikes without a technical recession).

## Impact
Model probabilities have no demonstrated out-of-sample skill on recent years. They must be shown as analytical estimates with this track record, never as reliable forecasts.

## Protocol note (honesty)
The held-out numbers of the first run (v1 features) were seen before the term spread was added (ADR-0015). The change was motivated by development diagnostics and the literature, and it did not improve held-out results, but the 2015+ period is no longer a perfectly untouched test set. Any further model change must be judged on development data or on new data arriving after 2026-11-09.

## Action
Phase 6 shows the held-out check next to every probability. Candidate improvements, to be evaluated on development data only: national short rates / credit spreads, OECD CLI (where published), confidence indicators, first-release (vintage) data, country-specific intercepts; possibly treating 2020 as a structural break in reporting.

Related: [[Evaluation protocol]] · [[ADR-0015 Publish only what beats the baseline]]
