Task: write a tiny dependency-free SVG sparkline for the KPI cards of the Next.js app.

## Files
- CREATE `apps/web/src/components/charts/sparkline.tsx` — the only file you write.
- CONTEXT (provided below, do not change): `apps/web/src/components/charts/sparkline.test.tsx` — the
  tests are the specification; read every assertion, including exact path strings.
  `apps/web/src/components/model/probability-gauge.tsx` shows the code style of the project.

## API
```tsx
export interface SparklineGeometry {
  /** Pixel positions of the finite values only, oldest first. */
  points: [number, number][];
  /** SVG path of the line. */
  line: string;
  /** SVG path of the filled area below the line (closed along the bottom edge). */
  area: string;
  /** Position of the newest finite value. */
  last: [number, number];
  /** y of the value 0 when min < 0 < max, otherwise null. */
  zeroY: number | null;
}

export function sparklineGeometry(
  values: readonly (number | null | undefined)[],
  width: number,
  height: number,
  pad: number,
): SparklineGeometry | null;

export interface SparklineProps {
  /** Oldest → newest. null / undefined / NaN are gaps and are never interpolated. */
  values: readonly (number | null | undefined)[];
  ariaLabel: string;
  width?: number; // default 120 (viewBox units)
  height?: number; // default 36
  tone?: "accent" | "ok" | "warn" | "danger" | "neutral"; // default "accent"
  className?: string;
}

export function Sparkline(props: SparklineProps): JSX.Element | null;
```

## Rules
1. No "use client", no hooks except `useId` from react (for the gradient id), no libraries.
2. Geometry. Slot i of n values has x = pad + i * (width - 2 * pad) / (n - 1). With min/max over the
   finite values: y = pad + (max - v) / (max - min) * (height - 2 * pad). If max === min every y is
   height / 2. Round every coordinate to 2 decimals and print it without trailing zeros
   (`Number(x.toFixed(2))`), so 36 prints as "36" and 12.5 as "12.5".
3. `line`: "M x y" for the first point and for every point that follows a gap (a non-finite slot),
   otherwise "L x y"; segments joined by one space. See the tests for the exact format.
4. `area`: the path through ALL finite points using "L" between them (first one "M"), then
   " L <lastX> <height> L <firstX> <height> Z".
5. Fewer than two finite values → `sparklineGeometry` returns null and `Sparkline` returns null.
6. `Sparkline` renders
   `<svg viewBox="0 0 {width} {height}" role="img" aria-label={ariaLabel} preserveAspectRatio="none" className={className}>`
   containing, in this order:
   - `<defs>` with a vertical `<linearGradient>` (id from `useId()`, with ":" characters removed):
     stop 0% = tone colour with stopOpacity 0.35, stop 100% = tone colour with stopOpacity 0;
   - `<path data-part="area" d={area} fill="url(#id)" />`;
   - when `zeroY !== null`: `<line data-part="zero" x1={pad} x2={width - pad} y1={zeroY} y2={zeroY}
     stroke="var(--color-line-strong)" strokeWidth={1} strokeDasharray="2 3" vectorEffect="non-scaling-stroke" />`;
   - `<path data-part="line" d={line} fill="none" stroke={colour} strokeWidth={1.75}
     strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />`;
   - `<circle data-part="last" cx cy r={2.5} fill={colour} />`.
   The pad passed to `sparklineGeometry` is 4.
7. Tone colours are CSS variables, written exactly: accent "var(--color-accent)", ok "var(--color-ok)",
   warn "var(--color-warn)", danger "var(--color-danger)", neutral "var(--color-fg-muted)".
8. TypeScript strict, no `any`, no non-null assertions (`!`); `noUncheckedIndexedAccess` is on, so
   guard array reads. Import `type JSX` from "react".

## Checks
The lead runs `pnpm --filter @macropulse/web exec vitest run src/components/charts/sparkline.test.tsx`,
`tsc --noEmit` and ESLint.
