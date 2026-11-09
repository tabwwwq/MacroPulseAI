---
type: finding
id: F-005
severity: low
status: workaround
area: process
found: 2026-11-08
tags:
  - finding
---

# F-005 · Codex sandbox has no network

> [!finding] Low severity · workaround
> Codex's elevated Windows sandbox runs as a separate user: no outbound network (even with network enabled) and no per-user Python/uv.

## Impact
Codex cannot run live probes or the Python toolchain.

## Action
Brief Codex for code, docs and review; run probes and Python tooling on Claude's side — [[ADR-0009 Claude leads, Codex takes scoped side tasks]].

Related: [[Agent workflow]]
