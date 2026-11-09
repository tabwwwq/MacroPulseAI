---
type: decision
id: ADR-0004
date: 2026-11-08
status: accepted
area: tooling
tags:
  - decision
---

# ADR-0004 · ESLint 9 instead of 10

> [!decision] Decision
> Pin ESLint 9.39.5.

## Context
eslint-config-next pulls eslint-plugin-react, jsx-a11y and import, which do not yet support ESLint 10.

## Consequences
No peer-dependency breakage; upgrade with the plugins.
