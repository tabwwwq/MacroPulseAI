---
type: codex-run
name: local-chart-theme-tests
date: 2026-11-11
time: "19:40"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-chart-theme-tests

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 19:40. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```ts
> import { describe, expect, it } from "vitest";
>
> import {
>   chartTheme,
>   glowLine,
>   tooltipStyle,
>   verticalFade,
>   withAlpha,
>   zoomSliderStyle,
> } from "@/components/charts/theme";
>
> describe("withAlpha", () => {
>   it("converts a 6-digit hex colour to rgba with the given alpha", () => {
>     expect(withAlpha("#4cc3ff", 0.5)).toBe("rgba(76, 195, 255, 0.5)");
>   });
>
>   it("accepts upper-case hex digits", () => {
>     expect(withAlpha("#4CC3FF", 0.5)).toBe("rgba(76, 195, 255, 0.5)");
>   });
>
>   it("returns non-6-digit-hex colours unchanged", () => {
>     expect(withAlpha("rgb(1, 2, 3)", 0.5)).toBe("rgb(1, 2, 3)");
>     expect(withAlpha("#fff", 0.5)).toBe("#fff");
>     expect(withAlpha("red", 0.5)).toBe("red");
>   });
> });
>
> describe("verticalFade", () => {
>   it("builds a top-to-bottom linear gradient with two colour stops", () => {
>     expect(verticalFade("#3dd6a3", 0.3, 0)).toEqual({
>       type: "linear",
>       x: 0,
>       y: 0,
>       x2: 0,
>       y2: 1,
>       colorStops: [
>         { offset: 0, color: "rgba(61, 214, 163, 0.3)" },
>         { offset: 1, color: "rgba(61, 214, 163, 0)" },
>       ],
>     });
>   });
> });
>
> describe("glowLine", () => {
>   it("defaults to width 2.25 and keeps the colour", () => {
>     const line = glowLine("#4cc3ff");
>     expect(line.width).toBe(2.25);
>     expect(line.color).toBe("#4cc3ff");
>   });
>
>   it("glows in the same colour at 0.55 opacity", () => {
>     expect(glowLine("#4cc3ff").shadowColor).toBe("rgba(76, 195, 255, 0.55)");
>   });
>
>   it("respects an explicit width", () => {
>     expect(glowLine("#4cc3ff", 4).width).toBe(4);
>   });
> });
>
> describe("chartTheme", () => {
>   it("keeps every palette entry a 6-digit hex colour", () => {
>     for (const color of chartTheme.palette) {
>       expect(color).toMatch(/^#[0-9a-f]{6}$/i);
>     }
>   });
>
>   it("makes the first palette entry the accent", () => {
>     expect(chartTheme.palette[0]).toBe(chartTheme.accent);
>   });
>
>   it("uses an opaque 6-digit hex export background", () => {
>     expect(chartTheme.exportBackground).toMatch(/^#[0-9a-f]{6}$/i);
>   });
> });
>
> describe("zoomSliderStyle", () => {
>   it("is a slider that does not draw a miniature of the data", () => {
>     expect(zoomSliderStyle.type).toBe("slider");
>     expect(zoomSliderStyle.showDataShadow).toBe(false);
>   });
> });
>
> describe("tooltipStyle", () => {
>   it("shows light text on a non-transparent background", () => {
>     expect(tooltipStyle.textStyle.color).toBe("#e7ebf3");
>     expect(tooltipStyle.backgroundColor.endsWith(", 0)")).toBe(false);
>   });
> });
> ```
>
> - `withAlpha` alpha is interpolated as a number, so `0.3` renders as `0.3` and `0` as `0` in the template string; asserted exactly.
> - `verticalFade` uses `toEqual` on the full object to pin the gradient direction and both stops.
> - `glowLine` shadow colour computed by hand from `#4cc3ff` → `rgba(76, 195, 255, 0.55)`.
> - `chartTheme` palette/accent/exportBackground validated with a 6-digit hex regex rather than re-deriving values.
> - `tooltipStyle` background checked via `endsWith(", 0)")` per the brief (it is `rgba(16, 24, 43, 0.94)`).

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the unit tests for the shared chart theme helpers.
>
> ## Files
> - CREATE `apps/web/src/components/charts/theme.test.ts` — the only file you write (Vitest, no React).
> - CONTEXT (provided below, do not change): `apps/web/src/components/charts/theme.ts` (the code under test)
>   and `apps/web/src/components/charts/sparkline.test.tsx` (test style of the project).
>
> ## What to cover (one `describe` per export, short `it` names that state the behaviour)
> 1. `withAlpha`: "#4cc3ff" with 0.5 → "rgba(76, 195, 255, 0.5)"; upper-case hex works too; anything that
>    is not a 6-digit hex ("rgb(1, 2, 3)", "#fff", "red") is returned unchanged.
> 2. `verticalFade("#3dd6a3", 0.3, 0)`: a top-to-bottom linear gradient (x 0, y 0, x2 0, y2 1) with exactly
>    two colour stops, offset 0 = "rgba(61, 214, 163, 0.3)" and offset 1 = "rgba(61, 214, 163, 0)".
> 3. `glowLine`: default width 2.25; keeps the colour; the glow (`shadowColor`) is the same colour at
>    0.55 opacity; an explicit width is respected.
> 4. `chartTheme`: every entry of `palette` is a 6-digit hex colour; the first one equals `accent`;
>    `exportBackground` is opaque (a 6-digit hex) — PNG exports must not be transparent.
> 5. `zoomSliderStyle`: it is a slider and does not draw a miniature of the data (`showDataShadow` false).
> 6. `tooltipStyle`: text colour "#e7ebf3" on a background that is NOT fully transparent (does not end
>    with ", 0)").
>
> ## Rules
> - `import { describe, expect, it } from "vitest";` and import the helpers from "@/components/charts/theme".
> - Assert exact values computed by hand from the source; do not re-implement the functions in the test.
> - TypeScript strict, no `any`. Output only the file in ONE fenced code block.
>
> # Output file
>
> `apps/web/src/components/charts/theme.test.ts`
>
> # Context files
>
> ## `apps/web/src/components/charts/theme.ts`
>
> ```ts
> /**
>  * Shared look of every ECharts canvas. Matches the tokens in globals.css — canvas rendering cannot
>  * consume Tailwind classes or CSS variables. Charts are transparent so the card surface shows
>  * through; PNG exports are flattened onto `exportBackground`.
>  */
> export const chartTheme = {
>   exportBackground: "#131b2c",
>   palette: ["#4cc3ff", "#3dd6a3", "#f2667a", "#8f8bff", "#a0abc0"],
>   accent: "#4cc3ff",
>   ok: "#3dd6a3",
>   warn: "#f5b544",
>   textStyle: { color: "#a0abc0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" },
>   gridLine: "#24304a",
>   axis: "#8a95ad",
> } as const;
>
> /** `#rrggbb` → `rgba(r, g, b, alpha)`; other colour notations are returned unchanged. */
> export function withAlpha(color: string, alpha: number): string {
>   const hex = /^#([0-9a-f]{6})$/i.exec(color)?.[1];
>   if (!hex) return color;
>   const n = Number.parseInt(hex, 16);
>   return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
> }
>
> /** Vertical fade from `color` at `from` opacity (top) to `to` (bottom): area fills and bars. */
> export function verticalFade(color: string, from: number, to: number) {
>   return {
>     type: "linear" as const,
>     x: 0,
>     y: 0,
>     x2: 0,
>     y2: 1,
>     colorStops: [
>       { offset: 0, color: withAlpha(color, from) },
>       { offset: 1, color: withAlpha(color, to) },
>     ],
>   };
> }
>
> /** Line with a soft glow in its own colour. */
> export function glowLine(color: string, width = 2.25) {
>   return { color, width, shadowColor: withAlpha(color, 0.55), shadowBlur: 10, shadowOffsetY: 4 };
> }
>
> /** Floating tooltip: dark glass panel with a hairline border. */
> export const tooltipStyle = {
>   backgroundColor: "rgba(16, 24, 43, 0.94)",
>   borderColor: "#34425f",
>   borderWidth: 1,
>   padding: [10, 12] as [number, number],
>   textStyle: { ...chartTheme.textStyle, color: "#e7ebf3", fontSize: 12, lineHeight: 18 },
>   extraCssText: "border-radius: 12px; box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.9);",
> } as const;
>
> /** Crosshair shown with axis tooltips. */
> export const axisPointerStyle = {
>   type: "line" as const,
>   lineStyle: { color: withAlpha(chartTheme.accent, 0.55), width: 1, type: "dashed" as const },
> };
>
> export const legendStyle = {
>   type: "scroll" as const,
>   top: 4,
>   icon: "roundRect",
>   itemWidth: 14,
>   itemHeight: 4,
>   itemGap: 18,
>   textStyle: chartTheme.textStyle,
>   pageIconColor: chartTheme.accent,
>   pageTextStyle: chartTheme.textStyle,
> } as const;
>
> export const categoryAxisStyle = {
>   axisLine: { lineStyle: { color: chartTheme.gridLine } },
>   axisTick: { show: false },
>   axisLabel: { color: chartTheme.axis, hideOverlap: true },
>   splitLine: { show: false },
> } as const;
>
> export const valueAxisStyle = {
>   axisLine: { show: false },
>   axisTick: { show: false },
>   axisLabel: { color: chartTheme.axis },
>   splitLine: { lineStyle: { color: chartTheme.gridLine, type: [3, 5] as number[] } },
> } as const;
>
> /** Range slider under time charts: a slim track, no miniature of the data. */
> export const zoomSliderStyle = {
>   type: "slider" as const,
>   bottom: 6,
>   height: 14,
>   borderColor: "transparent",
>   backgroundColor: "rgba(11, 16, 32, 0.7)",
>   fillerColor: withAlpha(chartTheme.accent, 0.22),
>   showDataShadow: false,
>   showDetail: false,
>   handleSize: "140%",
>   handleStyle: { color: "#e7ebf3", borderColor: chartTheme.accent, borderWidth: 1 },
>   moveHandleSize: 0,
>   brushSelect: false,
>   textStyle: chartTheme.textStyle,
> };
>
> ```
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
>     expect(g?.area).toBe("M 4 36 L 5
> …(truncated)
