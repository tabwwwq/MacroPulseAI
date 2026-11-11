---
type: codex-run
name: local-sparkline
date: 2026-11-11
time: "19:30"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-sparkline

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 19:30. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ````markdown
> ```tsx
> import { useId, type JSX } from "react";
>
> export interface SparklineGeometry {
>   /** Pixel positions of the finite values only, oldest first. */
>   points: [number, number][];
>   /** SVG path of the line. */
>   line: string;
>   /** SVG path of the filled area below the line (closed along the bottom edge). */
>   area: string;
>   /** Position of the newest finite value. */
>   last: [number, number];
>   /** y of the value 0 when min < 0 < max, otherwise null. */
>   zeroY: number | null;
> }
>
> const PAD = 4;
>
> export function sparklineGeometry(
>   values: readonly (number | null | undefined)[],
>   width: number,
>   height: number,
>   pad: number,
> ): SparklineGeometry | null {
>   const n = values.length;
>
>   // First pass: collect finite slots and their min/max.
>   const finite: { index: number; v: number }[] = [];
>   let min = Infinity;
>   let max = -Infinity;
>
>   for (let i = 0; i < n; i += 1) {
>     const raw = values[i];
>     if (typeof raw !== "number" || !Number.isFinite(raw)) continue;
>     finite.push({ index: i, v: raw });
>     if (raw < min) min = raw;
>     if (raw > max) max = raw;
>   }
>
>   if (finite.length < 2) return null;
>
>   // Second pass: compute x and y for each finite slot using the full range.
>   const pts: { x: number; y: number; index: number }[] = finite.map((f) => {
>     const x = n > 1 ? pad + (f.index * (width - 2 * pad)) / (n - 1) : width / 2;
>     const y = max === min ? height / 2 : pad + ((max - f.v) / (max - min)) * (height - 2 * pad);
>     return { x: round2(x), y: round2(y), index: f.index };
>   });
>
>   const points: [number, number][] = pts.map((p) => [p.x, p.y]);
>   const lastPt = pts[pts.length - 1];
>   const last: [number, number] = [lastPt?.x ?? 0, lastPt?.y ?? 0];
>
>   // Build the line path: "M" for the first point and for every point that
>   // follows a gap (i.e. its slot index is not exactly one more than the
>   // previous finite point's slot index), "L" otherwise.
>   const line = pts
>     .map((p, i) => {
>       const gap = i === 0 || p.index !== pts[i - 1]?.index + 1;
>       return `${gap ? "M" : "L"} ${p.x} ${p.y}`;
>     })
>     .join(" ");
>
>   const firstX = pts[0]?.x ?? 0;
>   const area =
>     pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") +
>     ` L ${last[0]} ${round2(height)} L ${firstX} ${round2(height)} Z`;
>
>   const zeroY = min < 0 && max > 0 ? round2(pad + ((max - 0) / (max - min)) * (height - 2 * pad)) : null;
>
>   return { points, line, area, last, zeroY };
> }
>
> function round2(x: number): number {
>   return Number(x.toFixed(2));
> }
>
> export interface SparklineProps {
>   /** Oldest → newest. null / undefined / NaN are gaps and are never interpolated. */
>   values: readonly (number | null | undefined)[];
>   ariaLabel: string;
>   width?: number; // default 120 (viewBox units)
>   height?: number; // default 36
>   tone?: "accent" | "ok" | "warn" | "danger" | "neutral"; // default "accent"
>   className?: string;
> }
>
> const TONE_COLOUR: Record<NonNullable<SparklineProps["tone"]>, string> = {
>   accent: "var(--color-accent)",
>   ok: "var(--color-ok)",
>   warn: "var(--color-warn)",
>   danger: "var(--color-danger)",
>   neutral: "var(--color-fg-muted)",
> };
>
> export function Sparkline(props: SparklineProps): JSX.Element | null {
>   const { values, ariaLabel, width = 120, height = 36, tone = "accent", className } = props;
>
>   // Hooks must be called unconditionally, before any early return.
>   const rawId = useId();
>   const gradientId = rawId.replace(/:/g, "");
>
>   const geometry = sparklineGeometry(values, width, height, PAD);
>   if (geometry === null) return null;
>
>   const colour = TONE_COLOUR[tone];
>
>   return (
>     <svg
>       viewBox={`0 0 ${width} ${height}`}
>       role="img"
>       aria-label={ariaLabel}
>       preserveAspectRatio="none"
>       className={className}
>     >
>       <defs>
>         <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
>           <stop offset="0%" stopColor={colour} stopOpacity={0.35} />
>           <stop offset="100%" stopColor={colour} stopOpacity={0} />
>         </linearGradient>
>       </defs>
>       <path data-part="area" d={geometry.area} fill={`url(#${gradientId})`} />
>       {geometry.zeroY !== null ? (
>         <line
>           data-part="zero"
>           x1={PAD}
>           x2={width - PAD}
>           y1={geometry.zeroY}
>           y2={geometry.zeroY}
>           stroke="var(--color-line-strong)"
>           strokeWidth={1}
>           strokeDasharray="2 3"
>           vectorEffect="non-scaling-stroke"
>         />
>       ) : null}
>       <path
>         data-part="line"
>         d={geometry.line}
>         fill="none"
>         stroke={colour}
>         strokeWidth={1.75}
>         strokeLinecap="round"
>         strokeLinejoin="round"
>         vectorEffect="non-scaling-stroke"
>       />
>       <circle data-part="last" cx={geometry.last[0]} cy={geometry.last[1]} r={2.5} fill={colour} />
>     </svg>
>   );
> }
> ```
> ````
>
> - Two-pass geometry: first collect finite slots + min/max, then compute coordinates, so every point uses the full range.
> - Gap detection now compares each finite point's original slot index to the previous finite point's slot index (`index !== prev.index + 1`), not the filtered-array position.
> - `useId()` moved to the top of `Sparkline` before the null check to satisfy `react-hooks/rules-of-hooks`.
> - Slot validity check uses `typeof raw === "number" && Number.isFinite(raw)` so `Infinity`/`-Infinity` are treated as gaps.
> - Introduced `const PAD = 4` and used it for both the `sparklineGeometry` call and the zero-line `x1`/`x2`.

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write a tiny dependency-free SVG sparkline for the KPI cards of the Next.js app.
>
> ## Files
> - CREATE `apps/web/src/components/charts/sparkline.tsx` — the only file you write.
> - CONTEXT (provided below, do not change): `apps/web/src/components/charts/sparkline.test.tsx` — the
>   tests are the specification; read every assertion, including exact path strings.
>   `apps/web/src/components/model/probability-gauge.tsx` shows the code style of the project.
>
> ## API
> ```tsx
> export interface SparklineGeometry {
>   /** Pixel positions of the finite values only, oldest first. */
>   points: [number, number][];
>   /** SVG path of the line. */
>   line: string;
>   /** SVG path of the filled area below the line (closed along the bottom edge). */
>   area: string;
>   /** Position of the newest finite value. */
>   last: [number, number];
>   /** y of the value 0 when min < 0 < max, otherwise null. */
>   zeroY: number | null;
> }
>
> export function sparklineGeometry(
>   values: readonly (number | null | undefined)[],
>   width: number,
>   height: number,
>   pad: number,
> ): SparklineGeometry | null;
>
> export interface SparklineProps {
>   /** Oldest → newest. null / undefined / NaN are gaps and are never interpolated. */
>   values: readonly (number | null | undefined)[];
>   ariaLabel: string;
>   width?: number; // default 120 (viewBox units)
>   height?: number; // default 36
>   tone?: "accent" | "ok" | "warn" | "danger" | "neutral"; // default "accent"
>   className?: string;
> }
>
> export function Sparkline(props: SparklineProps): JSX.Element | null;
> ```
>
> ## Rules
> 1. No "use client", no hooks except `useId` from react (for the gradient id), no libraries.
> 2. Geometry. Slot i of n values has x = pad + i * (width - 2 * pad) / (n - 1). With min/max over the
>    finite values: y = pad + (max - v) / (max - min) * (height - 2 * pad). If max === min every y is
>    height / 2. Round every coordinate to 2 decimals and print it without trailing zeros
>    (`Number(x.toFixed(2))`), so 36 prints as "36" and 12.5 as "12.5".
> 3. `line`: "M x y" for the first point and for every point that follows a gap (a non-finite slot),
>    otherwise "L x y"; segments joined by one space. See the tests for the exact format.
> 4. `area`: the path through ALL finite points using "L" between them (first one "M"), then
>    " L <lastX> <height> L <firstX> <height> Z".
> 5. Fewer than two finite values → `sparklineGeometry` returns null and `Sparkline` returns null.
> 6. `Sparkline` renders
>    `<svg viewBox="0 0 {width} {height}" role="img" aria-label={ariaLabel} preserveAspectRatio="none" className={className}>`
>    containing, in this order:
>    - `<defs>` with a vertical `<linearGradient>` (id from `useId()`, with ":" characters removed):
>      stop 0% = tone colour with stopOpacity 0.35, stop 100% = tone colour with stopOpacity 0;
>    - `<path data-part="area" d={area} fill="url(#id)" />`;
>    - when `zeroY !== null`: `<line data-part="zero" x1={pad} x2={width - pad} y1={zeroY} y2={zeroY}
>      stroke="var(--color-line-strong)" strokeWidth={1} strokeDasharray="2 3" vectorEffect="non-scaling-stroke" />`;
>    - `<path data-part="line" d={line} fill="none" stroke={colour} strokeWidth={1.75}
>      strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />`;
>    - `<circle data-part="last" cx cy r={2.5} fill={colour} />`.
>    The pad passed to `sparklineGeometry` is 4.
> 7. Tone colours are CSS variables, written exactly: accent "var(--color-accent)", ok "var(--color-ok)",
>    warn "var(--color-warn)", danger "var(--color-danger)", neutral "var(--color-fg-muted)".
> 8. TypeScript strict, no `any`, no non-null assertions (`!`); `noUncheckedIndexedAccess` is on, so
>    guard array reads. Import `type JSX` from "react".
>
> ## Checks
> The lead runs `pnpm --filter @macropulse/web exec vitest run src/components/charts/sparkline.test.tsx`,
> `tsc --noEmit` and ESLint.
>
> # Output file
>
> `apps/web/src/components/charts/sparkline.tsx`
>
> # Context files
>
> ## `apps/web/src/components/charts/sparkline.test.tsx`
>
> ```tsx
> import { render, screen } from "@testing-library/react";
> import { describe, expect, it } from "vitest";
>
> import { Sparkline, sparklineGeometry } from "@/components/charts/sparkline";
>
> describe("sparklineGeometry", () => {
>   it("maps the oldest value to the left edge and the newest to the right, highest value on top", () => {
>     const g = sparklineGeometry([0, 10, 5], 100, 40, 4);
>     expect(g).not.toBeNull();
>     expect(g?.points).toEqual([
>       [4, 36],
>       [50, 4],
>       [96, 20],
>     ]);
>     expect(g?.last).toEqual([96, 20]);
>     expect(g?.line).toBe("M 4 36 L 50 4 L 96 20");
>     // the area closes the line down to the bottom edge
>     expect(g?.area).toBe("M 4 36 L 50 4 L 96 20 L 96 40 L 4 40 Z");
>   });
>
>   it("draws a flat series in the vertical middle", () => {
>     const g = sparklineGeometry([2, 2, 2], 100, 40, 4);
>     expect(g?.points.map(([, y]) => y)).toEqual([20, 20, 20]);
>   });
>
>   it("reports the y position of zero only when zero lies strictly inside the value range", () => {
>     expect(sparklineGeometry([-10, 10], 100, 40, 4)?.zeroY).toBe(20);
>     expect(sparklineGeometry([1, 3], 100, 40, 4)?.zeroY).toBeNull();
>     expect(sparklineGeometry([0, 3], 100, 40, 4)?.zeroY).toBeNull();
>   });
>
>   it("skips missing values without inventing points and keeps their x slot empty", () => {
>     const g = sparklineGeometry([0, null, 10, Number.NaN, 5], 100, 40, 4);
>     expect(g?.points).toEqual([
>       [4, 36],
>       [50, 4],
>       [96, 20],
>     ]);
>     // a gap starts a new sub-path instead of drawing a line across it
>     expect(g?.line).toBe("M 4 36 M 50 4 M 96 20");
>   });
>
>   it("returns null with fewer than two finite values", () => {
>     expect(sparklineGeometry([], 100, 40, 4)).toBeNull();
>     expect(sparklineGeometry([3], 100, 40, 4)).toBeNull();
>     expect(sparklineGeometry([null, 3, null], 100, 40, 4)).toBeNull();
>   });
> });
>
> describe("Sparkline", () => {
>   it("renders an image with the given accessible name, a line, an area and an end marker", () => {
>     const { container
> …(truncated)
