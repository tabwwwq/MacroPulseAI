---
type: finding
id: F-003
severity: low
status: resolved
area: tooling
found: 2026-11-08
tags:
  - finding
---

# F-003 · Windows Python TLS to EU endpoints

> [!finding] Low severity · resolved
> Python's urllib on Windows raised `CERTIFICATE_VERIFY_FAILED` for Eurostat and ECB (missing on-demand root certificates).

## Impact
Initial probe could not reach two key sources.

## Action
Resolved by using the certifi CA bundle — [[ADR-0008 certifi CA bundle for official endpoints]].

Related: [[Eurostat]] · [[ECB]]
