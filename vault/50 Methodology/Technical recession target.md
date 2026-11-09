---
type: methodology
status: specified
tags:
  - methodology
  - ml
aliases:
  - Target definition
---

# 📐 Technical recession target

> [!important] Definition
> At an explicit `as_of` quarter *t*, the label for horizon **H ∈ {2, 4}** is **1** if at least one pair of **consecutive** quarters with **negative** quarter-on-quarter real-GDP growth lies **entirely inside** quarters *t+1 … t+H*; otherwise **0**.

## Rules
- Growth = q/q change of seasonally and calendar adjusted real GDP (`namq_10_gdp`, `CLV20_MNAC`, `SCA` — [[Eurostat]]; `GDPC1` — [[FRED]]).
- **Zero growth is not negative.**
- **Missing GDP** in the window → no trustworthy label (excluded, not 0).
- **Censoring:** a label exists only once the whole horizon has been observed; recent quarters are unlabelled.
- For H=2 the only qualifying pair is (*t+1*, *t+2*); for H=4 any adjacent pair in *t+1 … t+4*.

## Not the same as an official recession
US NBER recession dates (`USREC`) are an **external reference only** — shown separately, never used as the training target. A technical recession can occur without an NBER recession and vice versa.

## Edge cases to test (Phase 5)
| Case | Expected |
| --- | --- |
| `-0.1, -0.2` in *t+1, t+2* | 1 for H=2 and H=4 |
| `-0.1, 0.0, -0.2` | 0 (zero breaks the pair) |
| `+0.3, -0.1, -0.1, +0.2` | 0 for H=2, 1 for H=4 |
| Window extends past last observation | censored (no label) |
| Gap in GDP inside the window | excluded |

Related: [[Evaluation protocol]] · [[Phase 05 — Recession target, features & first model]]
