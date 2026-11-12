---
type: finding
id: F-017
severity: info
status: open
area: data
found: 2026-11-12
tags:
  - finding
---

# F-017 · ALFRED shows a 2022 technical recession that was revised away

> [!finding] Information · open
> Measured from the stored ALFRED vintages of US real GDP (GDPC1), live sync 2026-11-12.

## Evidence
- As first known on 2022-07-28 (advance estimate of 2022-Q2): q/q growth 2022-Q1 −0.40 %, 2022-Q2 −0.23 % → two consecutive negative quarters. In today's data: −0.25 % and **+0.14 %** → no technical recession.
- 2008-Q4, 2009-Q1, 2009-Q2 and 2020-Q2: signal both as first known and today.
- Over 140 genuine first releases (1991-Q4 onwards): mean absolute revision 0.29 pp, largest +1.62 pp (2020-Q2: −9.49 % first, −7.88 % today), 8 quarters changed sign.
- CPI y/y (650 first releases): mean |revision| 0.06 pp; unemployment (798): 0.07 pp, no sign changes.

## Why it matters
The recession models are trained and replayed on *today's* data. In 2022 the model would have been judged against a recession that, by first release, was there; the target itself moves with revisions. This supports keeping replays labelled as revised-data approximations ([[F-013 Replays show most recessions were missed]]) and is the case for vintage-backed US replays.

Related: [[ADR-0024 ALFRED vintages in separate tables with a first-release window]]
