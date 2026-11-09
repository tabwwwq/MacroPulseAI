---
type: decision
id: ADR-0008
date: 2026-11-08
status: accepted
area: data
tags:
  - decision
---

# ADR-0008 · certifi CA bundle for official endpoints

> [!decision] Decision
> Use the certifi (Mozilla) CA bundle — httpx does by default; the stdlib probe uses certifi when available.

## Context
Python on Windows failed TLS verification for Eurostat and ECB: the system store lacks roots that Windows downloads on demand only for its own apps.

## Consequences
TLS stays fully verified; no `verify=False` anywhere. See [[F-003 Windows Python TLS to EU endpoints]].
