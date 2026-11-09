---
type: decision
id: ADR-0010
date: 2026-11-09
status: accepted
area: process
tags:
  - decision
---

# ADR-0010 · Obsidian vault as project memory

> [!decision] Decision
> Keep an Obsidian vault in `vault/`: curated notes (status, phases, decisions, data, sessions) are versioned with the code; Claude Code hooks and the Codex runner log activity automatically into `80 Logs/` (git-ignored).

## Context
Decisions, evidence and progress were scattered across chat, docs and tool output.

## Consequences
Every session starts with the current status injected from [[Status]]; nothing is lost between sessions or agents.
