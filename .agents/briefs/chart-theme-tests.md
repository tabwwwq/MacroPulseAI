Task: write the unit tests for the shared chart theme helpers.

## Files
- CREATE `apps/web/src/components/charts/theme.test.ts` — the only file you write (Vitest, no React).
- CONTEXT (provided below, do not change): `apps/web/src/components/charts/theme.ts` (the code under test)
  and `apps/web/src/components/charts/sparkline.test.tsx` (test style of the project).

## What to cover (one `describe` per export, short `it` names that state the behaviour)
1. `withAlpha`: "#4cc3ff" with 0.5 → "rgba(76, 195, 255, 0.5)"; upper-case hex works too; anything that
   is not a 6-digit hex ("rgb(1, 2, 3)", "#fff", "red") is returned unchanged.
2. `verticalFade("#3dd6a3", 0.3, 0)`: a top-to-bottom linear gradient (x 0, y 0, x2 0, y2 1) with exactly
   two colour stops, offset 0 = "rgba(61, 214, 163, 0.3)" and offset 1 = "rgba(61, 214, 163, 0)".
3. `glowLine`: default width 2.25; keeps the colour; the glow (`shadowColor`) is the same colour at
   0.55 opacity; an explicit width is respected.
4. `chartTheme`: every entry of `palette` is a 6-digit hex colour; the first one equals `accent`;
   `exportBackground` is opaque (a 6-digit hex) — PNG exports must not be transparent.
5. `zoomSliderStyle`: it is a slider and does not draw a miniature of the data (`showDataShadow` false).
6. `tooltipStyle`: text colour "#e7ebf3" on a background that is NOT fully transparent (does not end
   with ", 0)").

## Rules
- `import { describe, expect, it } from "vitest";` and import the helpers from "@/components/charts/theme".
- Assert exact values computed by hand from the source; do not re-implement the functions in the test.
- TypeScript strict, no `any`. Output only the file in ONE fenced code block.
