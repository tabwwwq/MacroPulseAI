---
type: methodology
status: implemented
implemented: 2026-11-09
target_version: technical-recession-v1
tags:
  - methodology
  - ml
aliases:
  - Target definition
---

# 📐 Technical recession target

> [!important] Definition
> At an explicit `as_of` quarter *t*, the label for horizon **H ∈ {2, 4}** is **1** if at least one pair of **consecutive** quarters with **negative** quarter-on-quarter real-GDP growth lies **entirely inside** quarters *t+1 … t+H*; otherwise **0**.

## Rules (implemented in `packages/ml/src/macropulse_ml/target.py`)
- Growth = q/q change of seasonally and calendar adjusted real GDP (`namq_10_gdp`, `CLV20_MNAC`, `SCA` — [[Eurostat]]; `GDPC1` — [[FRED]]), latest revision.
- **Zero growth is not negative.**
- **Missing GDP** in the window → status `missing`, no label (excluded, not 0).
- **Censoring:** a window that reaches past the last observed quarter → status `censored`, no label.
- For H=2 the only qualifying pair is (*t+1*, *t+2*); for H=4 any adjacent pair in *t+1 … t+4*.

## Edge cases (all tested in `test_target.py`)
| Case | Expected |
| --- | --- |
| `-0.1, -0.2` in *t+1, t+2* | 1 for H=2 and H=4 |
| `-0.1, 0.0, -0.2` | 0 (zero breaks the pair) |
| `+0.3, -0.1, -0.1, +0.2` | 0 for H=2, 1 for H=4 |
| Negative *t* and *t+1* only | 0 for H=2 (the window starts at *t+1*) |
| Window extends past last observation | censored (no label) |
| Gap in GDP inside the window | excluded |

## Technical recessions in the stored data (revised GDP, 2026-11-09)
- **BE** 2001-Q3–Q4, 2008-Q3–2009-Q1, 2012-Q1–Q2, 2012-Q4–2013-Q1, 2020-Q1–Q2
- **DE** 1991-Q2–Q3, 1992-Q2–1993-Q1, 2001-Q2–2002-Q1, 2002-Q4–2003-Q1, 2004-Q3–Q4, 2008-Q2–2009-Q1, 2012-Q4–2013-Q1, 2019-Q4–2020-Q2, 2022-Q4–2023-Q2, 2025-Q2–Q3
- **FR** 2008-Q2–2009-Q1, 2012-Q1–Q2, 2019-Q4–2020-Q2
- **NL** 2008-Q3–2009-Q2, 2011-Q2–2013-Q1, 2020-Q1–Q2, 2022-Q4–2023-Q3
- **US** 1947, 1949, 1953–54, 1957–58, 1969–70, 1974–75, 1980, 1981–82, 1990–91, 2008–09, 2020 (2001 is *not* a technical recession in revised data — its negative quarters were not consecutive)

## Not the same as an official recession
US NBER recession dates (`USREC`) are an **external reference only** — shown separately, never a feature or the training target. A technical recession can occur without an NBER recession and vice versa.

Related: [[Evaluation protocol]] · [[Phase 05 — Recession target, features & first model]]
