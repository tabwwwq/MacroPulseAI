---
type: finding
id: F-004
severity: medium
status: open
area: data
found: 2026-11-08
tags:
  - finding
---

# F-004 · World Bank central-government debt is sparse

> [!finding] Medium severity · open
> `GC.DOD.TOTL.GD.ZS` has 0–5 observations for BE, DE, FR, NL (US: 36).

## Impact
Unusable as a fiscal feature for the euro-area countries.

## Action
Use Eurostat quarterly general-government debt (`gov_10q_ggdebt`); never splice different debt scopes.

Related: [[World Bank]] · [[Eurostat]]
