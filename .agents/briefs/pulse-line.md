Task: write a small decorative "heartbeat" line (the MacroPulse brand motif) for page headers.

## Files
- CREATE `apps/web/src/components/ui/pulse-line.tsx` — the only file you write.
- CONTEXT (provided below, do not change): `apps/web/src/components/ui/pulse-line.test.tsx` — the tests
  are the specification, including the exact path strings. `apps/web/src/components/charts/sparkline.tsx`
  shows the project's code style.

## API
```tsx
/** ECG-like polyline across a width x height box: flat baseline with `beats` evenly spaced heartbeats. */
export function pulsePath(width: number, height: number, beats: number): string;

export function PulseLine({ className }: { className?: string }): JSX.Element;
```

## pulsePath rules
- Baseline y = 0.6 * height. The path starts "M 0 <baseline>".
- Beat k (k = 0 … beats-1) is centred at cx = (k + 0.5) * width / beats and adds exactly five vertices:
  (cx - 16, baseline), (cx - 8, baseline - 0.12 * height), (cx, baseline - 0.48 * height),
  (cx + 8, baseline + 0.28 * height), (cx + 16, baseline).
- The path ends with "L <width> <baseline>".
- Every vertex is written "L x y"; numbers rounded to 2 decimals without trailing zeros
  (`Number(n.toFixed(2))`); tokens separated by single spaces. With 0 beats: "M 0 <baseline> L <width> <baseline>".

## PulseLine rules
- No "use client". The only hook is `useId` from react (ids for the gradient and the filter; remove ":").
- `<svg viewBox="0 0 600 120" preserveAspectRatio="none" aria-hidden="true" focusable="false"
  fill="none" className={className}>` — purely decorative.
- `const d = pulsePath(600, 120, 3)`.
- `<defs>`: a horizontal `<linearGradient>` with stops 0 % "var(--color-iris)", 50 % "var(--color-accent)",
  100 % "var(--color-ok)"; and a `<filter>` with `<feGaussianBlur stdDeviation="3" />`
  (x="-10%" y="-50%" width="120%" height="200%").
- Children, in this order:
  1. `<path data-part="base" d={d} stroke="var(--color-line-strong)" strokeWidth={1.25}
     vectorEffect="non-scaling-stroke" />`
  2. a blurred copy of the trace for the glow: same `d`, stroke = the gradient, strokeWidth 4,
     strokeDasharray "70 190", className "animate-trace", opacity 0.7, filter = the blur filter,
     strokeLinecap "round". No data-part on this one.
  3. `<path data-part="trace" d={d} stroke={gradient} strokeWidth={1.75} strokeLinecap="round"
     strokeLinejoin="round" strokeDasharray="70 190" className="animate-trace"
     vectorEffect="non-scaling-stroke" />`
- TypeScript strict, no `any`, no `!`; import `type JSX` from "react". Output only the file, in ONE
  fenced code block (three backticks, language tsx) — do not nest fences.
