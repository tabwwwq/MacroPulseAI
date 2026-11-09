# Brief: ECharts time-series chart + ChartFrame (Phase 2 design system)

## Goal
Build the reusable chart layer for MacroPulse's web app: a lean ECharts wrapper and a `ChartFrame` card that
handles every honest state (loading, error, empty, stale, ready) plus working table view and CSV/PNG export.
Today no economic observations exist, so most pages will render `ChartFrame` with `series=[]`; real data
arrives in Phase 4. Never ship sample/fake series in the app — fixtures belong in tests only.

## Files you may create (and nothing else)
- `apps/web/src/components/charts/types.ts`
- `apps/web/src/components/charts/time-series-chart.tsx`
- `apps/web/src/components/charts/chart-frame.tsx`
- `apps/web/src/components/charts/data-table.tsx`
- `apps/web/src/lib/export.ts`
- `apps/web/src/lib/export.test.ts`
- `apps/web/src/components/charts/chart-frame.test.tsx`

Do not edit package.json/lockfiles (echarts 6.1.0 and all Radix packages are already installed), shared UI
primitives, pages, or anything else. Reuse existing primitives read-only: `@/components/ui/button`
(`Button`, `buttonVariants`), `@/components/ui/badge` (`Badge`), `@/components/ui/card` (`Card`,
`CardHeader`, `CardBody`), `@/components/ui/skeleton`, `@/components/ui/states` (`ErrorState`, `EmptyState`),
`@/lib/cn`, `@/lib/format` (`formatDateTimeUtc`). Design tokens are in `apps/web/src/app/globals.css`
(`--color-*`): read them via CSS variables or hard-code the same hex values only inside the ECharts theme
object (ECharts cannot read CSS classes).

## Contract (implement exactly; the lead engineer codes pages against it in parallel)

```ts
// types.ts
export interface SeriesPoint { period: string; value: number | null }   // "2026-Q3", "2026-09" or ISO date
export interface ChartSeries { id: string; name: string; unit: string; points: SeriesPoint[] }
export interface ChartShading { from: string; to: string; label: string }  // e.g. external NBER reference
export interface ChartSource { label: string; href?: string; retrievedAt?: string | null }
export type ChartKind = "line" | "bar";

// time-series-chart.tsx  ("use client")
export interface TimeSeriesChartProps {
  series: ChartSeries[]; kind?: ChartKind; height?: number; shading?: ChartShading[]; ariaLabel: string;
}
export function TimeSeriesChart(props: TimeSeriesChartProps): JSX.Element
// also export a ref handle or callback so ChartFrame can get a PNG data URL (echarts getDataURL)

// chart-frame.tsx  ("use client")
export interface ChartFrameProps {
  title: string;
  description?: ReactNode;
  series: ChartSeries[];
  isLoading?: boolean;
  error?: unknown;              // rendered with <ErrorState error onRetry>
  onRetry?: () => void;
  emptyTitle?: string;          // default "No observations yet"
  emptyMessage?: ReactNode;
  source?: ChartSource;         // footnote: "Source: … · retrieved …"
  staleSince?: string | null;   // when set and data exists: amber "Stale" badge + note
  allowKindToggle?: boolean;    // line/bar toggle
  defaultKind?: ChartKind;
  shading?: ChartShading[];
  height?: number;              // default 280
  exportName: string;           // base file name for CSV/PNG
}
export function ChartFrame(props: ChartFrameProps): JSX.Element

// lib/export.ts
export function seriesToCsv(series: ChartSeries[]): string   // columns: period,<series name (unit)>...; union of periods, sorted; empty cell for null/missing; RFC 4180 quoting
export function downloadText(filename: string, text: string, mime?: string): void
export function downloadDataUrl(filename: string, dataUrl: string): void
```

## Behaviour requirements
- ECharts: modular imports from `echarts/core` (LineChart, BarChart, GridComponent, TooltipComponent,
  LegendComponent, DataZoomComponent, MarkAreaComponent, CanvasRenderer) — not the full bundle. Init on mount,
  `setOption` on prop change, `ResizeObserver` → `resize()`, dispose on unmount. Dark theme from the tokens,
  tabular numbers, gaps for `null` values (`connectNulls: false`), never interpolate missing data.
  Respect `prefers-reduced-motion` (animation off).
- Shading renders as `markArea` with its label in the tooltip/legend; it must be visually distinct and labelled
  (it is used for external reference periods, not model output).
- Accessibility: the chart container has `role="img"` and `aria-label`; the Table toggle shows an accessible
  `<table>` (`data-table.tsx`) with caption, `scope` headers and the same values as the CSV.
- Toolbar (only shown when data exists): Line/Bar segmented toggle if `allowKindToggle`, "Table" toggle,
  "CSV" and "PNG" buttons that really download (`<title>.csv` / `.png` via `exportName`). When there is no
  data, render the empty state and NO enabled toolbar actions (disable with a `title` reason or omit).
- States precedence: loading skeleton → error (with retry) → empty → ready (+ stale badge when `staleSince`).
- Footnote shows `source.label` (link if `href`, `target=_blank rel="noopener noreferrer"`) and
  `retrievedAt` via `formatDateTimeUtc`.

## Tests (Vitest + Testing Library; jsdom has no canvas → mock `echarts/core` in chart tests)
- `seriesToCsv`: union/sort of periods, nulls → empty cells, quoting of commas/quotes, unit in header.
- `ChartFrame`: loading, error (retry button calls `onRetry`), empty (no enabled export buttons), ready
  (toolbar present; Table toggle shows a table with the fixture values; CSV click calls the download helper),
  stale badge only when data exists.
Run them with `node node_modules/vitest/vitest.mjs run` from `apps/web` (pnpm is not on your PATH), plus
`node node_modules/typescript/bin/tsc --noEmit -p .` and `node node_modules/eslint/bin/eslint.js src/components/charts src/lib/export.ts`.
Report exact results.
