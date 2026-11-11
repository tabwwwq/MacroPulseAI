---
type: decision
id: ADR-0023
date: 2026-11-11
status: accepted
area: web
tags:
  - decision
---

# ADR-0023 · Opaque panels, shared chart theme and decorative motion

> [!decision] Decision
> The visual refresh keeps every text surface **opaque** (the `panel` utility: navy gradient fill inside a 1 px gradient border) and puts all atmosphere — aurora glows, grid, pulse trace, glow shadows — into `aria-hidden`, pointer-transparent layers. ECharts colours and styles live in one module, `components/charts/theme.ts`. A second accent (`--color-iris`) is allowed in gradients only, never to carry meaning.

## Why
- "Glass" cards with translucent fills would make text contrast depend on whatever glow sits behind them; axe can only report such text as *needs review*. Opaque fills keep the WCAG AA guarantee from [[F-015 Accessibility violations found by the first axe run]] testable.
- Three chart components each carried their own copy of the colours (one still had the pre-F-015 subtle grey `#7f8aa3`). One theme module removes the drift; canvases are now transparent and PNG exports are flattened onto `exportBackground`.
- KPI sparklines draw the stored series the KPI value comes from (the same query as the overview charts), ending at the KPI's own period — no decorative fake trend. Gaps stay gaps.
- Motion (page rise, shimmer, aurora drift, pulse trace) is decoration only and is switched off by the existing `prefers-reduced-motion` block.

## Consequences
- New surfaces use `panel` (+ `panel-hover` when interactive) instead of ad-hoc `border bg-surface` classes; reference: `docs/DESIGN.md`.
- The risk bands, status badges and chart series keep their colours and their text labels; nothing about the data or the wording of caveats changed.
- Components written by the local model for this refresh: `Sparkline`, the redesigned `ProbabilityGauge`, `PulseLine`, the chart-theme tests and the first draft of `docs/DESIGN.md` ([[ADR-0021 Local model as a reviewed single-file worker]]).

Related: [[Phase 10 — Hardening & release]]
