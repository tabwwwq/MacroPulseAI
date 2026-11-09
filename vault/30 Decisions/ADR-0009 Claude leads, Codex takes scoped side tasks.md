---
type: decision
id: ADR-0009
date: 2026-11-08
status: accepted
area: process
tags:
  - decision
---

# ADR-0009 · Claude leads, Codex takes scoped side tasks

> [!decision] Decision
> Claude Code owns architecture, the task list and verification. Codex receives written briefs listing the only files it may touch, via `scripts/agents/codex-task.ps1`. Every result is reviewed before acceptance.

## Context
Two coding agents are available; parallel work must not collide and must stay verifiable.

## Consequences
Codex's Windows sandbox has no network and no per-user Python, so live probes and Python tooling run on Claude's side. See [[Agent workflow]] and [[F-005 Codex sandbox has no network]].
