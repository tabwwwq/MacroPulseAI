---
type: finding
id: F-014
severity: medium
status: resolved
area: tooling
found: 2026-11-10
tags:
  - finding
---

# F-014 · Agentic Codex on the local model was unproductive

> [!finding] Medium severity · resolved by a different workflow
> Codex CLI 0.167 pointed at the local llama.cpp server (Qwen3.8-27B Q3_K_XL, 32k context) answered a read-only smoke question correctly, but on the first real task (write `reports/charts.py`) it ran about 25 shell commands — reading `pyproject.toml`, listing the repo, grepping imports, re-reading the fixture — for 31 minutes and wrote nothing before the session was interrupted (both processes exited with code 4).

## Evidence
- `.agents/codex-runs/20261110-235440-report-charts.log`: exec/read commands only, no patch.
- Server log: generation slowed to about 13.5 tokens/s as the context grew; llama-server skipped Codex's `namespace` and `web_search` tool types.
- Codex logged `failed to refresh available models` (llama-server's model list format); harmless.

## Resolution
Single-file delegation with all context in one request (`scripts/agents/local_task.py`): the same charts task took 55 s per round ([[ADR-0021 Local model as a reviewed single-file worker]]). Also fixed on the way: a q8_0 KV cache with flash attention fell back to the CPU on Vulkan (prompt processing 6.7 tok/s); the f16 cache runs at about 410 tok/s.

Related: [[Phase 09 — Analyst-grade PDF reports]]
