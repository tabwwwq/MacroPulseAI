---
type: decision
id: ADR-0001
date: 2026-11-08
status: accepted
area: architecture
tags:
  - decision
---

# ADR-0001 · pnpm + uv monorepo

> [!decision] Decision
> Use a pnpm workspace (`apps/web`, `packages/shared-types`) and a uv workspace (`apps/api`, `packages/economics`) with committed lockfiles.

## Context
The product needs a Next.js frontend and a Python data/ML backend in one reproducible repo.

## Consequences
One clone, two package managers with fast, locked installs; root `package.json` scripts orchestrate both (`pnpm dev`, `pnpm test`, `pnpm lint`).
