---
type: finding
id: F-002
severity: medium
status: mitigated
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

## Recheck 2026-11-12
- `DSD_STES@DF_CLI` 4.1, exact key `{ISO3}.M.LI.IX._Z.AA.IX._Z.H` (amplitude adjusted, OECD harmonised): DEU, FRA and USA return the CLI; BEL and NLD still return only `BCICP` (composite business confidence) and `CCICP` (composite consumer confidence).
- Mitigation: the OECD connector syncs the CLI for DE, FR and US, and the two confidence indices as **separate indicators** for all five countries. Confidence is never labelled as a CLI; BE/NL keep `cli` = *not published*.

Related: [[OECD]] · [[ADR-0027 OECD connector with confidence indicators kept apart from the CLI]]
