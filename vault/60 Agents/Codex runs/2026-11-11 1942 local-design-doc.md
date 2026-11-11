---
type: codex-run
name: local-design-doc
date: 2026-11-11
time: "19:42"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-design-doc

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 19:42. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ````markdown
> # MacroPulse design system
>
> MacroPulse uses a dark navy "research terminal" look. Design tokens live in `apps/web/src/app/globals.css` inside the Tailwind v4 `@theme` block. ECharts canvases cannot read CSS variables, so the same values are mirrored in `apps/web/src/components/charts/theme.ts`.
>
> ## Principles
>
> - Opaque card fill: text contrast never depends on what is behind the panel.
> - Meaning is never conveyed by colour alone; semantic colours are paired with text or an icon.
> - The second accent (`iris`) is decorative only, used for gradients and glows, never for meaning.
> - Decorative layers are `aria-hidden` and ignore the pointer.
> - Motion is optional; a `prefers-reduced-motion` block disables it.
>
> ## Colour tokens
>
> | Token | Value | Use |
> |---|---|---|
> | `--color-canvas` | `#0b1020` | Page background (`bg-canvas`) |
> | `--color-surface` | `#131b2c` | Card fill; chart `exportBackground` |
> | `--color-surface-2` | `#172238` | Secondary fill (`bg-surface-2`) |
> | `--color-elevated` | `#1c2840` | Elevated fill (`bg-elevated`) |
> | `--color-line` | `#24304a` | Hairline and grid lines |
> | `--color-line-strong` | `#34425f` | Stronger borders; chart tooltip border |
> | `--color-fg` | `#e7ebf3` | Primary text (`text-fg`) |
> | `--color-fg-muted` | `#a0abc0` | Muted text (`text-fg-muted`) |
> | `--color-fg-subtle` | `#8a95ad` | Subtle text (`text-fg-subtle`) |
> | `--color-accent` | `#4cc3ff` | Primary accent |
> | `--color-accent-strong` | `#2f9bff` | Stronger accent |
> | `--color-iris` | `#8f8bff` | Decorative gradients and glows only |
> | `--color-ok` | `#3dd6a3` | Positive state |
> | `--color-warn` | `#f5b544` | Warning state |
> | `--color-danger` | `#f2667a` | Danger state |
>
> ## Shape, shadow and type
>
> - `--radius-card`: `1rem` — card corner radius.
> - `--shadow-card`: inset top highlight, 1px bottom shadow, and a soft drop shadow.
> - `--shadow-glow`: accent ring plus a blue glow, used on hover.
> - `--font-sans`: `var(--font-inter), ui-sans-serif, system-ui, sans-serif`.
> - `--font-mono`: `var(--font-plex-mono), ui-monospace, SFMono-Regular, Menlo, monospace`.
> - `tabular` utility: sets `font-variant-numeric: tabular-nums` for aligned numerals.
>
> ## Surfaces and utilities
>
> | Class | What it does | Used by |
> |---|---|---|
> | `panel` | Opaque navy card fill inside a 1px gradient border; `--shadow-card` | `Card`, `KpiCard` |
> | `panel-hover` | Lifts and adds `--shadow-glow` on hover / focus-within | `KpiCard` |
> | `hairline` | 1px line fading out at both ends | — |
> | `text-headline` | White-to-accent gradient text with a readable fallback colour | `PageHeader` |
> | `aurora` | Fixed decorative backdrop: two glows and a faint grid; `pointer-events: none` | — |
> | `shimmer` | Loading placeholder with a moving highlight | — |
> | `page-enter` | Rises content in once per route | — |
>
> ## Motion
>
> | Token | Duration | Purpose |
> |---|---|---|
> | `--animate-rise` | 0.5s | Content rises in once per route |
> | `--animate-shimmer` | 1.6s | Moving highlight on loading placeholders |
> | `--animate-drift` | 28s | Slow drift of the aurora backdrop |
> | `--animate-trace` | 4.5s | Tracing dash along the pulse line |
>
> The `prefers-reduced-motion: reduce` block forces animation and transition durations to `0.01ms`, sets `animation-iteration-count` to 1, and disables smooth scrolling, so all motion is effectively off.
>
> ## Charts
>
> | Export | Purpose |
> |---|---|
> | `chartTheme` | Shared colours, palette and text style for every canvas |
> | `withAlpha` | Convert a `#rrggbb` colour to `rgba` with an alpha |
> | `verticalFade` | Vertical gradient for area fills and bars |
> | `glowLine` | Line style with a soft glow in its own colour |
> | `tooltipStyle` | Dark glass tooltip panel with a hairline border |
> | `axisPointerStyle` | Dashed crosshair for axis tooltips |
> | `legendStyle` | Scrollable legend with rounded icons |
> | `categoryAxisStyle` | Category axis: quiet line, no ticks or split lines |
> | `valueAxisStyle` | Value axis: dashed split lines, no axis line |
> | `zoomSliderStyle` | Slim range slider under time charts |
>
> PNG exports are flattened onto `exportBackground` because the canvases are transparent.
>
> ## Components
>
> ### Card
>
> `Card` renders a `section` with the `panel` class and `min-w-0`. `CardHeader` holds a title, optional description and an optional `action` slot. `CardBody` provides the padded content area.
>
> ### Button
>
> `Button` uses `cva` with three variants and three sizes.
>
> - Variants: `primary` (gradient fill, `text-canvas`), `secondary` (bordered, `bg-surface-2`), `ghost` (text only).
> - Sizes: `sm` (`h-8 px-3`), `md` (`h-9 px-4`), `icon` (`size-9`).
> - Defaults: `variant: "secondary"`, `size: "md"`.
>
> ### PageHeader
>
> `PageHeader` shows an optional `eyebrow`, a `title` using `text-headline`, an optional `description` and an optional `meta` slot. A decorative `PulseLine` sits behind the right half of the header.
>
> ### KpiCard
>
> `KpiCard` is a `panel panel-hover` article. It renders a label, a formatted `value` (or an explicit unavailable state), an optional `change` chip, a `badge`, `period`, `flag`, `note` and `source` with a provenance tooltip. The `trend` prop draws a `Sparkline` of stored observations; gaps stay gaps.
>
> ### Sparkline
>
> `Sparkline` renders an SVG line with a gradient area fill and an end marker. `null`, `undefined` and `NaN` values are gaps and are never interpolated. `sparklineGeometry` computes the line, area, last point and zero line.
>
> ### PulseLine
>
> `PulseLine` is a decorative ECG-like polyline with a gradient stroke and a tracing dash. It is `aria-hidden` and `focusable="false"`, so it is hidden from assistive technology.
>
> ## Adding a component: checklist
>
> - [ ] Use an opaque `panel` fill so text contrast never depends on the backdrop.
> - [ ] Pair every semantic colour with text or an icon; never rely on colour alone.
> - [ ] Reserve `iris` for decorative gradients and glows, not for meaning.
> - [ ] Mark decorative layers `aria-hidden` and set `pointer-events: none`.
> - [ ] Keep motion optional and confirm it is di
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the design-system reference of the web app as Markdown.
>
> ## Files
> - CREATE `docs/DESIGN.md` — the only file you write.
> - CONTEXT (provided below, do not change; they are the ONLY source of truth): `apps/web/src/app/globals.css`,
>   `apps/web/src/components/charts/theme.ts`, `apps/web/src/components/ui/card.tsx`,
>   `apps/web/src/components/ui/button.tsx`, `apps/web/src/components/ui/page-header.tsx`,
>   `apps/web/src/components/data/kpi-card.tsx`, `apps/web/src/components/charts/sparkline.tsx`,
>   `apps/web/src/components/ui/pulse-line.tsx`.
>
> ## Hard rules
> - Document ONLY what is in the context files. Never invent a token, class, colour value, component, prop or
>   file. Copy colour values and class names exactly. If something is not in the context, leave it out.
> - No marketing language, no emojis. Short, factual sentences in British English. No screenshots.
> - At most 170 lines. Tables for tokens. Code only as short inline `code`, plus at most two fenced examples.
>
> ## Structure (use exactly these H2 headings, in this order)
> # MacroPulse design system
> One paragraph: dark "research terminal" look; tokens live in `apps/web/src/app/globals.css` (Tailwind v4
> `@theme`); ECharts canvases cannot read CSS variables, so the same values are mirrored in
> `apps/web/src/components/charts/theme.ts`.
>
> ## Principles
> 5 bullets taken from the comments in the context files: opaque card fill so text contrast never depends
> on the backdrop; meaning never by colour alone; the second accent (iris) is decorative only; decorative
> layers are `aria-hidden` and ignore the pointer; motion is optional (reduced-motion block).
>
> ## Colour tokens
> Table: Token | Value | Use. Every `--color-*` variable from `@theme`, with the use described by the
> comments in globals.css or by how the context components use the Tailwind class (e.g. `text-fg-muted`).
>
> ## Shape, shadow and type
> `--radius-card`, `--shadow-card`, `--shadow-glow`, the two font variables and the `tabular` utility.
>
> ## Surfaces and utilities
> Table: Class | What it does | Used by — for `panel`, `panel-hover`, `hairline`, `text-headline`, `aurora`,
> `shimmer`, `page-enter`. "Used by" only where a context file shows it.
>
> ## Motion
> Table of the `--animate-*` tokens with duration and purpose, and one paragraph on the
> `prefers-reduced-motion` block.
>
> ## Charts
> Table of the exports of `theme.ts` (name | purpose). State that PNG exports are flattened onto
> `exportBackground` because the canvases are transparent.
>
> ## Components
> Short subsections (H3) for Card, Button (its three variants and three sizes exactly as defined), PageHeader,
> KpiCard (the `trend` prop draws a `Sparkline` of stored observations; gaps stay gaps), Sparkline, PulseLine
> (decorative, hidden from assistive technology).
>
> ## Adding a component: checklist
> 6–8 checklist items (`- [ ]`) derived from the principles above.
>
> Because the file contains fenced examples, wrap your whole answer file in a FOUR-backtick fence
> (````markdown … ````).
>
> # Output file
>
> `docs/DESIGN.md`
>
> # Context files
>
> ## `apps/web/src/app/globals.css`
>
> ```css
> @import "tailwindcss";
>
> /* ----------------------------------------------------------------------------------------------
>    MacroPulse design tokens. Dark navy research-terminal palette; every text/background pair used
>    for body copy meets WCAG AA (fg-muted on surface ≈ 7:1, fg-subtle on surface ≈ 4.8:1).
>    Semantic colours are always paired with text or an icon — never colour alone.
>    ---------------------------------------------------------------------------------------------- */
> @theme {
>   --color-canvas: #0b1020;
>   --color-surface: #131b2c;
>   --color-surface-2: #172238;
>   --color-elevated: #1c2840;
>   --color-line: #24304a;
>   --color-line-strong: #34425f;
>
>   --color-fg: #e7ebf3;
>   --color-fg-muted: #a0abc0;
>   --color-fg-subtle: #8a95ad;
>
>   --color-accent: #4cc3ff;
>   --color-accent-strong: #2f9bff;
>   /* Second accent: only for decorative gradients and glows, never for meaning. */
>   --color-iris: #8f8bff;
>   --color-ok: #3dd6a3;
>   --color-warn: #f5b544;
>   --color-danger: #f2667a;
>
>   --radius-card: 1rem;
>   --shadow-card:
>     inset 0 1px 0 0 rgb(255 255 255 / 0.05), 0 1px 0 0 rgb(0 0 0 / 0.3), 0 24px 48px -28px rgb(0 0 0 / 0.85);
>   --shadow-glow: 0 0 0 1px rgb(76 195 255 / 0.22), 0 18px 50px -22px rgb(47 155 255 / 0.55);
>
>   --animate-rise: rise 0.5s cubic-bezier(0.2, 0.7, 0.2, 1) both;
>   --animate-shimmer: shimmer 1.6s linear infinite;
>   --animate-drift: drift 28s ease-in-out infinite alternate;
>   --animate-trace: trace 4.5s linear infinite;
>
>   @keyframes rise {
>     from {
>       opacity: 0;
>       transform: translateY(10px);
>     }
>     to {
>       opacity: 1;
>       transform: translateY(0);
>     }
>   }
>
>   @keyframes shimmer {
>     from {
>       background-position: 200% 0;
>     }
>     to {
>       background-position: -200% 0;
>     }
>   }
>
>   @keyframes drift {
>     from {
>       transform: translate3d(-2%, -1%, 0) scale(1);
>     }
>     to {
>       transform: translate3d(3%, 2%, 0) scale(1.08);
>     }
>   }
>
>   @keyframes trace {
>     from {
>       stroke-dashoffset: 0;
>     }
>     to {
>       stroke-dashoffset: -260;
>     }
>   }
> }
>
> @theme inline {
>   --font-sans: var(--font-inter), ui-sans-serif, system-ui, sans-serif;
>   --font-mono: var(--font-plex-mono), ui-monospace, SFMono-Regular, Menlo, monospace;
> }
>
> @layer base {
>   html {
>     color-scheme: dark;
>     scrollbar-color: var(--color-line-strong) transparent;
>     scrollbar-width: thin;
>   }
>
>   body {
>     @apply bg-canvas font-sans text-fg antialiased;
>     font-feature-settings: "cv11", "ss01";
>   }
>
>   ::selection {
>     background: rgb(76 195 255 / 0.3);
>   }
>
>   :focus-visible {
>     outline: 2px solid var(--color-accent);
>     outline-offset: 2px;
>   }
>
>   /* Tables: quiet mono column heads, rows light up under the pointer. */
>   thead th {
>     font-family: var(--font-mono);
>     font-size: 11px;
>     letter-spacing: 0.08em;
>     text-transform: uppercase;
>   }
>
>   tbody tr {
>     transition: background-color 0.15s ease;
>   }
>
>   tbody tr:hover {
>     background-c
> …(truncated)
