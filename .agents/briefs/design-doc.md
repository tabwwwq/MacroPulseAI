Task: write the design-system reference of the web app as Markdown.

## Files
- CREATE `docs/DESIGN.md` — the only file you write.
- CONTEXT (provided below, do not change; they are the ONLY source of truth): `apps/web/src/app/globals.css`,
  `apps/web/src/components/charts/theme.ts`, `apps/web/src/components/ui/card.tsx`,
  `apps/web/src/components/ui/button.tsx`, `apps/web/src/components/ui/page-header.tsx`,
  `apps/web/src/components/data/kpi-card.tsx`, `apps/web/src/components/charts/sparkline.tsx`,
  `apps/web/src/components/ui/pulse-line.tsx`.

## Hard rules
- Document ONLY what is in the context files. Never invent a token, class, colour value, component, prop or
  file. Copy colour values and class names exactly. If something is not in the context, leave it out.
- No marketing language, no emojis. Short, factual sentences in British English. No screenshots.
- At most 170 lines. Tables for tokens. Code only as short inline `code`, plus at most two fenced examples.

## Structure (use exactly these H2 headings, in this order)
# MacroPulse design system
One paragraph: dark "research terminal" look; tokens live in `apps/web/src/app/globals.css` (Tailwind v4
`@theme`); ECharts canvases cannot read CSS variables, so the same values are mirrored in
`apps/web/src/components/charts/theme.ts`.

## Principles
5 bullets taken from the comments in the context files: opaque card fill so text contrast never depends
on the backdrop; meaning never by colour alone; the second accent (iris) is decorative only; decorative
layers are `aria-hidden` and ignore the pointer; motion is optional (reduced-motion block).

## Colour tokens
Table: Token | Value | Use. Every `--color-*` variable from `@theme`, with the use described by the
comments in globals.css or by how the context components use the Tailwind class (e.g. `text-fg-muted`).

## Shape, shadow and type
`--radius-card`, `--shadow-card`, `--shadow-glow`, the two font variables and the `tabular` utility.

## Surfaces and utilities
Table: Class | What it does | Used by — for `panel`, `panel-hover`, `hairline`, `text-headline`, `aurora`,
`shimmer`, `page-enter`. "Used by" only where a context file shows it.

## Motion
Table of the `--animate-*` tokens with duration and purpose, and one paragraph on the
`prefers-reduced-motion` block.

## Charts
Table of the exports of `theme.ts` (name | purpose). State that PNG exports are flattened onto
`exportBackground` because the canvases are transparent.

## Components
Short subsections (H3) for Card, Button (its three variants and three sizes exactly as defined), PageHeader,
KpiCard (the `trend` prop draws a `Sparkline` of stored observations; gaps stay gaps), Sparkline, PulseLine
(decorative, hidden from assistive technology).

## Adding a component: checklist
6–8 checklist items (`- [ ]`) derived from the principles above.

Because the file contains fenced examples, wrap your whole answer file in a FOUR-backtick fence
(````markdown … ````).
