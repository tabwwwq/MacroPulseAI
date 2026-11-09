---
type: decision
id: ADR-0006
date: 2026-11-08
status: accepted
area: data
tags:
  - decision
---

# ADR-0006 · SQLite locally, PostgreSQL in production

> [!decision] Decision
> Local development uses SQLite (`data/local/macropulse.db`); migrations are written portably (naming convention, batch mode); CI runs the same migrations and API tests against PostgreSQL.

## Context
Docker is not installed on the development machine, but production must use PostgreSQL.

## Consequences
Frictionless Windows setup; PostgreSQL compatibility is proven in CI rather than assumed.
