---
type: decision
id: ADR-0021
date: 2026-11-11
status: accepted
area: tooling
tags:
  - decision
---

# ADR-0021 · Local model as a reviewed single-file worker

> [!decision] Decision
> The user asked for coding work to be done by a local open-weight model with Claude reviewing and correcting it. The local model (Qwen3.8-27B, Q3_K_XL, llama.cpp Vulkan on the RX 7800 XT) receives **one fully specified file per task**: the brief, the context files and, for revisions, the review feedback, in a single request (`scripts/agents/local_task.py`). Claude writes the contract and the specification tests first, runs every check, looks at real output, and either sends written feedback or corrects the file itself.

## Why
- Agentic Codex on the same model (`codex-task.ps1 -Local`) spent 31 minutes reading files without writing anything ([[F-014 Agentic Codex on the local model was unproductive]]). One request with all context takes 30 s to 3.5 min.
- The script can only write the named output file, so the model cannot touch anything else; every run is logged and recorded in the vault.
- Tests alone were not enough: two bugs in the model's PDF code (ragged table rows, misaligned spans) and several layout problems were found only by reading the code and rasterising real PDFs.

## Consequences
- Good fit: small modules with a typed interface and tests (charts, CSV, PDF layout, a React view).
- Lead keeps: contracts, data assembly, anything touching data correctness, security, concurrency and the final call.
- Review effort is real: in Phase 9, 7 model rounds and 9 lead corrections (`docs/LOCAL_MODEL.md`).

Related: [[ADR-0009 Claude leads, Codex takes scoped side tasks]] · [[Phase 09 — Analyst-grade PDF reports]]
