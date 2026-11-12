---
type: finding
id: F-018
severity: info
status: open
area: ml
found: 2026-11-12
tags:
  - finding
---

# F-018 · First-release figures hid the 2008 downturn and amplified the 2022 false alarm

> [!finding] Information · open
> Vintage replay on the stored ALFRED vintages, run `20261112T150103Z` (H=2 HistGradientBoosting, H=4 MLP). Every listed quarter reproduced its stored estimate before the first-release inputs were scored.

## Evidence (4 quarters ahead, revised data → as first published)
| As-of | Revised data | First published | Main input change |
|---|---|---|---|
| 2007-Q4 | 12.6 % | 7.1 % | GDP q/q 0.58 → **1.20** |
| 2008-Q2 | 2.2 % | 0.7 % | 2008-Q1 GDP q/q **−0.43 → +0.24**, negative quarters 1 → 0 |
| 2019-Q4 | 11.8 % | 8.5 % | GDP q/q 1.17 → 0.52 |
| 2020-Q1 | 25.0 % | 29.5 % | GDP y/y 3.35 → 2.33 |
| 2022-Q3 | 75.3 % | **85.4 %** | 2022-Q1/Q2 −0.25 / +0.14 → −0.41 / −0.14 (two negative quarters) |

Two quarters ahead the pattern is the same: 2008-Q2 1.1 % → 0.2 %, 2022-Q3 21.6 % → 33.3 %.

## Why it matters
Real-time data made the model's 2008 miss worse (the slump was not yet in the figures) and its 2022 false alarm stronger (the "recession" of [[F-017 ALFRED shows a 2022 technical recession that was revised away]]). Replays on revised data therefore flatter the model before 2008 and understate how alarmed it would have been in 2022.

Related: [[ADR-0025 Vintage replay re-fits the stored fold model]], [[F-013 Replays show most recessions were missed]]
