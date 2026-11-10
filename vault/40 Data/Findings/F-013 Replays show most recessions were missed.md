---
type: finding
id: F-013
severity: high
status: open
area: ml
found: 2026-11-10
tags:
  - finding
---

# F-013 · Replays show most recessions were missed

> [!finding] High severity · open
> Counting realised technical recessions since the first walk-forward fold (all five countries, run `20261110T142434Z`, 50 % line, warning window = the H − 1 quarters before the first negative quarter):
> - **2-quarter model (HistGradientBoosting): warned before 0 of 20** evaluable recessions; 7 false-alarm episodes.
> - **4-quarter model (Logistic Regression): warned before 6 of 22**, missed 16; 26 false-alarm episodes, 10 of them during or right after a recession.

## Evidence
| Country | 4Q warned | 4Q missed | 4Q false-alarm episodes (after a recession) |
|---|---|---|---|
| BE | 1 (2008-Q3) | 4 | 5 (1) |
| DE | 3 (2008-Q2, 2022-Q4, 2025-Q2) | 5 | 8 (4) |
| FR | 1 (2008-Q2) | 2 | 5 (1) |
| NL | 1 (2022-Q4) | 3 | 5 (3) |
| US | 0 | 2 | 3 (1) |

Examples visible on `/history`: US as of 2019-Q4, 4Q estimate 18.1 % before COVID (missed); DE as of 2008-Q2, 28.3 % (missed — the recession had started in that very quarter, still unpublished); DE as of 2022-Q3, 83.7 % (warned).

## Interpretation
The 2-quarter model is almost never above 50 %; its probabilities are low and smooth, so the threshold view shows it as never warning. Several 4-quarter false alarms are the model reacting to a slump that has already happened, while the next four quarters recover. COVID-2020 is not foreseeable from these inputs at all. This matches [[F-008 No model beats the base rate on held-out years]] from a different angle.

## Action
Shown, not hidden: every recession and false alarm is listed with a link to its replay, and the counts sit on the page. Model work (Phase 10 or later) should be judged on development years only and on this view as well as Brier skill — e.g. a lower, pre-registered warning threshold for the 2-quarter model, or features for slumps already under way.

Related: [[ADR-0019 Replays are walk-forward fold estimates]] · [[F-012 Recession model lowers risk when unemployment rises]]
