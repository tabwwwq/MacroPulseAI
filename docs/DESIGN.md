# MacroPulse design system

MacroPulse uses a dark navy "research terminal" look. Design tokens live in `apps/web/src/app/globals.css` inside the Tailwind v4 `@theme` block. ECharts canvases cannot read CSS variables, so the same values are mirrored in `apps/web/src/components/charts/theme.ts`.

> Drafted by the local model (Qwen3.8-27B) from the source files, then reviewed against them by the lead;
> the "Used by" column and the verification section were completed in review. See [LOCAL_MODEL.md](LOCAL_MODEL.md).

## Principles

- Opaque card fill: text contrast never depends on what is behind the panel.
- Meaning is never conveyed by colour alone; semantic colours are paired with text or an icon.
- The second accent (`iris`) is decorative only, used for gradients and glows, never for meaning.
- Decorative layers are `aria-hidden` and ignore the pointer.
- Motion is optional; a `prefers-reduced-motion` block disables it.

## Colour tokens

| Token | Value | Use |
|---|---|---|
| `--color-canvas` | `#0b1020` | Page background (`bg-canvas`) |
| `--color-surface` | `#131b2c` | Card fill; chart `exportBackground` |
| `--color-surface-2` | `#172238` | Secondary fill (`bg-surface-2`) |
| `--color-elevated` | `#1c2840` | Elevated fill (`bg-elevated`) |
| `--color-line` | `#24304a` | Hairline and grid lines |
| `--color-line-strong` | `#34425f` | Stronger borders; chart tooltip border |
| `--color-fg` | `#e7ebf3` | Primary text (`text-fg`) |
| `--color-fg-muted` | `#a0abc0` | Muted text (`text-fg-muted`) |
| `--color-fg-subtle` | `#8a95ad` | Subtle text (`text-fg-subtle`) |
| `--color-accent` | `#4cc3ff` | Primary accent |
| `--color-accent-strong` | `#2f9bff` | Stronger accent |
| `--color-iris` | `#8f8bff` | Decorative gradients and glows only |
| `--color-ok` | `#3dd6a3` | Positive state |
| `--color-warn` | `#f5b544` | Warning state |
| `--color-danger` | `#f2667a` | Danger state |

## Shape, shadow and type

- `--radius-card`: `1rem` — card corner radius.
- `--shadow-card`: inset top highlight, 1px bottom shadow, and a soft drop shadow.
- `--shadow-glow`: accent ring plus a blue glow, used on hover.
- `--font-sans`: `var(--font-inter), ui-sans-serif, system-ui, sans-serif`.
- `--font-mono`: `var(--font-plex-mono), ui-monospace, SFMono-Regular, Menlo, monospace`.
- `tabular` utility: sets `font-variant-numeric: tabular-nums` for aligned numerals.

## Surfaces and utilities

| Class | What it does | Used by |
|---|---|---|
| `panel` | Opaque navy card fill inside a 1px gradient border; `--shadow-card` | `Card`, `KpiCard` |
| `panel-hover` | Lifts and adds `--shadow-glow` on hover / focus-within | `KpiCard`, country tiles |
| `hairline` | 1px line fading out at both ends | `Topbar` (bottom edge), footer (top edge), section headings |
| `text-headline` | White-to-accent gradient text with a readable fallback colour | `PageHeader` |
| `aurora` | Fixed decorative backdrop: two glows and a faint grid; `pointer-events: none` | `AppShell` (one `aria-hidden` layer behind the content column) |
| `shimmer` | Loading placeholder with a moving highlight | `Skeleton` |
| `page-enter` | Rises content in once per route | `AppShell` (content wrapper keyed by pathname, so filters do not replay it) |

## Motion

| Token | Duration | Purpose |
|---|---|---|
| `--animate-rise` | 0.5s | Content rises in once per route |
| `--animate-shimmer` | 1.6s | Moving highlight on loading placeholders |
| `--animate-drift` | 28s | Slow drift of the aurora backdrop |
| `--animate-trace` | 4.5s | Tracing dash along the pulse line |

The `prefers-reduced-motion: reduce` block forces animation and transition durations to `0.01ms`, sets `animation-iteration-count` to 1, and disables smooth scrolling, so all motion is effectively off.

## Charts

| Export | Purpose |
|---|---|
| `chartTheme` | Shared colours, palette and text style for every canvas |
| `withAlpha` | Convert a `#rrggbb` colour to `rgba` with an alpha |
| `verticalFade` | Vertical gradient for area fills and bars |
| `glowLine` | Line style with a soft glow in its own colour |
| `tooltipStyle` | Dark glass tooltip panel with a hairline border |
| `axisPointerStyle` | Dashed crosshair for axis tooltips |
| `legendStyle` | Scrollable legend with rounded icons |
| `categoryAxisStyle` | Category axis: quiet line, no ticks or split lines |
| `valueAxisStyle` | Value axis: dashed split lines, no axis line |
| `zoomSliderStyle` | Slim range slider under time charts |

PNG exports are flattened onto `exportBackground` because the canvases are transparent.

## Components

### Card

`Card` renders a `section` with the `panel` class and `min-w-0`. `CardHeader` holds a title, optional description and an optional `action` slot. `CardBody` provides the padded content area.

### Button

`Button` uses `cva` with three variants and three sizes.

- Variants: `primary` (gradient fill, `text-canvas`), `secondary` (bordered, `bg-surface-2`), `ghost` (text only).
- Sizes: `sm` (`h-8 px-3`), `md` (`h-9 px-4`), `icon` (`size-9`).
- Defaults: `variant: "secondary"`, `size: "md"`.

### PageHeader

`PageHeader` shows an optional `eyebrow`, a `title` using `text-headline`, an optional `description` and an optional `meta` slot. A decorative `PulseLine` sits behind the right half of the header.

### KpiCard

`KpiCard` is a `panel panel-hover` article. It renders a label, a formatted `value` (or an explicit unavailable state), an optional `change` chip, a `badge`, `period`, `flag`, `note` and `source` with a provenance tooltip. The `trend` prop draws a `Sparkline` of stored observations; gaps stay gaps. `kpiTrend` (in `kpi-grid.tsx`) takes them from the same stored series as the value, ending at the KPI's own period, at most 24 observations.

### Sparkline

`Sparkline` renders an SVG line with a gradient area fill and an end marker. `null`, `undefined` and `NaN` values are gaps and are never interpolated. `sparklineGeometry` computes the line, area, last point and zero line.

### PulseLine

`PulseLine` is a decorative ECG-like polyline with a gradient stroke and a tracing dash. It is `aria-hidden` and `focusable="false"`, so it is hidden from assistive technology.

## Adding a component: checklist

- [ ] Use an opaque `panel` fill so text contrast never depends on the backdrop.
- [ ] Pair every semantic colour with text or an icon; never rely on colour alone.
- [ ] Reserve `iris` for decorative gradients and glows, not for meaning.
- [ ] Mark decorative layers `aria-hidden` and set `pointer-events: none`.
- [ ] Keep motion optional and confirm it is disabled under `prefers-reduced-motion`.
- [ ] Mirror any new colour into `theme.ts` if it is used on an ECharts canvas.
- [ ] Use `tabular` for aligned numerals and the mono font for data.
- [ ] Verify focus-visible outlines and keyboard access for interactive elements.

## Verification

- `pnpm --filter @macropulse/web exec playwright test`: every page at 1440 px and 375 px without console errors or horizontal overflow, and axe (WCAG 2.0/2.1 A and AA) with no serious or critical violation — 58/58 on this design (2026-11-11).
- Vitest covers `sparklineGeometry`, `Sparkline`, `pulsePath`, `PulseLine`, `kpiTrend`, the chart theme helpers and the gauge's accessible name.
