---
type: decision
id: ADR-0002
date: 2026-11-08
status: accepted
area: tooling
tags:
  - decision
---

# ADR-0002 · Python 3.12 instead of 3.15

> [!decision] Decision
> Pin Python 3.12 via `.python-version`; install it with `py install 3.12`; run everything through uv.

## Context
The machine's default Python is 3.15, which is too new for reliable wheels of the scientific stack (NumPy, scikit-learn, XGBoost, SHAP).

## Consequences
Predictable wheels and CI parity; use `py -3.12` or `uv run`, never the Microsoft Store `python` stub.
