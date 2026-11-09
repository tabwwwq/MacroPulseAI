---
type: decision
id: ADR-0003
date: 2026-11-08
status: accepted
area: tooling
tags:
  - decision
---

# ADR-0003 · TypeScript 6.0.3 instead of 7

> [!decision] Decision
> Pin TypeScript 6.0.3.

## Context
TypeScript 7 (native compiler) is the latest release, but Next.js type-checking and openapi-typescript expect the JS-based compiler API.

## Consequences
Builds and type generation work; revisit when Next.js and openapi-typescript support TS 7.
