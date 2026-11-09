---
type: finding
id: F-002
severity: medium
status: open
area: data
found: 2026-11-08
tags:
  - finding
---

# F-002 · OECD CLI missing for Belgium and Netherlands

> [!finding] Medium severity · open
> The OECD CLI dataflow returns the composite leading indicator (`LI`) for DE, FR and US, but only business/consumer confidence for BE and NL.

## Impact
The CLI feature is unavailable for BE/NL; confidence indices must not be relabelled as CLI.

## Action
Use a documented reduced feature set for BE/NL or keep partial model coverage.

Related: [[OECD]]
