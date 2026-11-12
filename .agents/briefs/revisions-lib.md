Task: write the pure helpers behind the "first release vs today" revision view of the web app.

## Files
- CREATE `apps/web/src/lib/revisions.ts` — the only file you write.
- CONTEXT (provided below, do not change): `apps/web/src/lib/revisions.test.ts` (the specification — read every
  assertion, including exact strings), `apps/web/src/lib/revisions.fixture.ts` (the API response shape),
  `apps/web/src/components/charts/types.ts` (`ChartSeries`), `apps/web/src/lib/series.ts` (code style).

## API
```ts
import type { RevisionPointOut, Revisions, TechnicalSignal } from "@macropulse/shared-types";
import type { ChartSeries } from "@/components/charts/types";

export function revisionChartSeries(data: Revisions): ChartSeries[];          // [first release, today's data]
export function largestRevisions(data: Revisions, n?: number): RevisionPointOut[]; // default n = 5
export function signalLabel(signal: TechnicalSignal): { label: string; tone: "neutral" | "warn" | "accent" };
export function formatSigned(value: number | null | undefined, digits?: number): string; // default 2
```

## Rules
1. Only points with `first_release === true` are used anywhere (back-filled history is excluded).
2. `revisionChartSeries`: points sorted by period (labels sort lexicographically, "2020-Q2" < "2022-Q1");
   series 1: id `${country}-${indicator.id}-first-release`, name "First release", values `first_value`;
   series 2: id `${country}-${indicator.id}-latest`, name "Today's data", values `latest_value` (null stays null).
   Both: `unit` = `data.indicator.unit`, `source` = `ALFRED · ${series.dataset}`, `citation` =
   `ALFRED (Federal Reserve Bank of St. Louis), ${dataset}; ${vintages} vintages ${first_vintage} to ${last_vintage}; retrieved ${retrieved_at.slice(0, 10)}`.
3. `largestRevisions`: points with a non-null `revision`, sorted by `Math.abs(revision)` descending, ties by
   period ascending; the first `n`.
4. `signalLabel`: both flags → "Confirmed by today's data" / "neutral"; only `as_first_known` → "Revised away" /
   "warn"; only `in_latest_data` → "Only visible in today's data" / "accent".
5. `formatSigned`: `Intl.NumberFormat("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits,
   signDisplay: "exceptZero" })`; non-finite or null/undefined → "N/A". Cache formatters per `digits` in a Map.
6. TypeScript strict with `noUncheckedIndexedAccess`; no `any`, no `!`; never mutate `data` (copy before sorting).

Output only the file, in ONE fenced code block (three backticks, language ts) — do not nest fences.
