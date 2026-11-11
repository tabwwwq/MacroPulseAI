Task: redesign the semicircular probability gauge of the recession page so it looks premium
(fintech terminal), without changing its API, its text or its accessibility.

## Files
- REWRITE `apps/web/src/components/model/probability-gauge.tsx` — the only file you write.
- CONTEXT (provided below, do not change): the current `probability-gauge.tsx`,
  `apps/web/src/components/model/model-components.test.tsx` (must keep passing), `apps/web/src/lib/risk.ts`.

## Keep exactly
- The export `ProbabilityGauge({ probability, band, bands, baseRate })` and its prop types.
- The `<svg role="img" aria-label={label}>` with the same `label` string as today.
- The `<figcaption>` texts: `formatProbability(probability)`, `{meta.label} risk band`, and the
  base-rate line "Dashed tick: base rate in the training sample, X" (only when `baseRate !== null`).
- No "use client"; the only hook allowed is `useId` from react (for SVG ids, strip ":" from it).

## New drawing (viewBox "0 0 200 118", R = 80, CX = 100, CY = 100)
Use the existing `point(p, radius)` and an `arc(from, to, radius = R)` helper. In this order:
1. `<defs>`: a Gaussian blur filter (`<filter id=... x="-30%" y="-30%" width="160%" height="160%">
   <feGaussianBlur stdDeviation="3.5" /></filter>`) used for glows.
2. Track: one arc from 0 to 1, stroke "#1c2840", strokeWidth 14, strokeLinecap "round".
3. Band segments: one arc per band, strokeWidth 10, strokeLinecap "butt", colour
   `BANDS[name]?.color ?? "#a0abc0"`, strokeOpacity 1 for the active band and 0.3 for the others.
   Leave a small gap between neighbours: shorten each segment by 0.006 at both ends, except the
   outer ends at 0 and 1.
4. Glow of the active band: the same arc as the active segment drawn BEFORE the segments, strokeWidth 14,
   strokeOpacity 0.55, with the blur filter. Mark it `aria-hidden`.
5. Tick marks at 0, 0.25, 0.5, 0.75 and 1: short lines from radius R + 10 to R + 14, stroke "#34425f",
   strokeWidth 1.5; and their labels "0%", "25%", "50%", "75%", "100%" at radius R + 22,
   fontSize 8, fill "#8a95ad", textAnchor "middle", dominantBaseline "middle".
6. Base-rate tick (when `baseRate !== null`): line from radius R - 9 to R + 9, stroke "#e7ebf3",
   strokeWidth 2, strokeDasharray "2 2".
7. Needle: a tapered polygon from the hub to the tip at radius R - 16. Base half-width 3.5 at the hub,
   perpendicular to the needle direction; fill "#e7ebf3". Behind it the same polygon in the active
   band colour with the blur filter and opacity 0.6 (`aria-hidden`).
8. Hub: circle r 7 fill "#131b2c" stroke "#e7ebf3" strokeWidth 2, then circle r 2.5 in the band colour.

## Caption styling
- Probability: `className="tabular font-mono text-[44px] font-semibold leading-none tracking-tight text-fg"`.
- Band line: keep `style={{ color: meta.color }}` and add a small coloured dot before the text
  (`<span aria-hidden className="mr-2 inline-block size-2 rounded-full align-middle" style={{ backgroundColor: meta.color, boxShadow: `0 0 10px ${meta.color}` }} />`).
  The visible text must stay exactly `{meta.label} risk band` in ONE text node (the test uses
  getByText("Moderate risk band")).
- SVG `className="w-full max-w-[300px]"`; figcaption `className="mt-1 text-center"`.

## Rules
TypeScript strict, `noUncheckedIndexedAccess` (guard array reads), no `any`, no `!` assertions, no unused
variables. Round coordinates with `toFixed(2)`. Output only the file.
