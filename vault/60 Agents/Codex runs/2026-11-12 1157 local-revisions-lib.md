---
type: codex-run
name: local-revisions-lib
date: 2026-11-12
time: "11:57"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-revisions-lib

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-12 11:57. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```ts
> import type { RevisionPointOut, Revisions, TechnicalSignal } from "@macropulse/shared-types";
>
> import type { ChartSeries } from "@/components/charts/types";
>
> const formatterCache = new Map<number, Intl.NumberFormat>();
>
> function getFormatter(digits: number): Intl.NumberFormat {
>   let f = formatterCache.get(digits);
>   if (!f) {
>     f = new Intl.NumberFormat("en-GB", {
>       minimumFractionDigits: digits,
>       maximumFractionDigits: digits,
>       signDisplay: "exceptZero",
>     });
>     formatterCache.set(digits, f);
>   }
>   return f;
> }
>
> export function formatSigned(value: number | null | undefined, digits = 2): string {
>   if (value === null || value === undefined || !Number.isFinite(value)) {
>     return "N/A";
>   }
>   return getFormatter(digits).format(value);
> }
>
> export function signalLabel(signal: TechnicalSignal): { label: string; tone: "neutral" | "warn" | "accent" } {
>   if (signal.as_first_known && signal.in_latest_data) {
>     return { label: "Confirmed by today's data", tone: "neutral" };
>   }
>   if (signal.as_first_known) {
>     return { label: "Revised away", tone: "warn" };
>   }
>   if (signal.in_latest_data) {
>     return { label: "Only visible in today's data", tone: "accent" };
>   }
>   return { label: "Not in either vintage", tone: "neutral" };
> }
>
> export function revisionChartSeries(data: Revisions): ChartSeries[] {
>   const points = data.points
>     .filter((p) => p.first_release)
>     .map((p) => ({ ...p }))
>     .sort((a, b) => (a.period < b.period ? -1 : a.period > b.period ? 1 : 0));
>
>   const { country, indicator, series } = data;
>   const unit = indicator.unit;
>   const source = `ALFRED · ${series.dataset}`;
>   const citation = `ALFRED (Federal Reserve Bank of St. Louis), ${series.dataset}; ${series.vintages} vintages ${series.first_vintage} to ${series.last_vintage}; retrieved ${series.retrieved_at.slice(0, 10)}`;
>
>   const first: ChartSeries = {
>     id: `${country}-${indicator.id}-first-release`,
>     name: "First release",
>     unit,
>     points: points.map((p) => ({ period: p.period, value: p.first_value })),
>     source,
>     citation,
>   };
>
>   const latest: ChartSeries = {
>     id: `${country}-${indicator.id}-latest`,
>     name: "Today's data",
>     unit,
>     points: points.map((p) => ({ period: p.period, value: p.latest_value })),
>     source,
>     citation,
>   };
>
>   return [first, latest];
> }
>
> export function largestRevisions(data: Revisions, n = 5): RevisionPointOut[] {
>   const ranked = data.points
>     .filter((p): p is RevisionPointOut & { revision: number } => p.first_release && p.revision !== null)
>     .map((p) => ({ ...p }))
>     .sort((a, b) => {
>       const diff = Math.abs(b.revision) - Math.abs(a.revision);
>       if (diff !== 0) return diff;
>       return a.period < b.period ? -1 : a.period > b.period ? 1 : 0;
>     });
>   return ranked.slice(0, n);
> }
> ```
>
> - `largestRevisions` uses a type predicate to narrow `revision` to `number` after the null check, avoiding `!` and `any` under strict mode.
> - `signalLabel` includes a defensive fourth branch (neither flag) returning a neutral label, since the spec only defines three cases but the flags are independent booleans.
> - `formatterCache` is a module-level `Map<number, Intl.NumberFormat>` keyed by `digits`, satisfying the "cache per digits" rule.
> - Sorting copies points via spread before sorting to guarantee no mutation of the input `data`.
> - `retrieved_at.slice(0, 10)` is used directly per the brief; the fixture value yields `2026-11-12` as asserted.

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the pure helpers behind the "first release vs today" revision view of the web app.
>
> ## Files
> - CREATE `apps/web/src/lib/revisions.ts` — the only file you write.
> - CONTEXT (provided below, do not change): `apps/web/src/lib/revisions.test.ts` (the specification — read every
>   assertion, including exact strings), `apps/web/src/lib/revisions.fixture.ts` (the API response shape),
>   `apps/web/src/components/charts/types.ts` (`ChartSeries`), `apps/web/src/lib/series.ts` (code style).
>
> ## API
> ```ts
> import type { RevisionPointOut, Revisions, TechnicalSignal } from "@macropulse/shared-types";
> import type { ChartSeries } from "@/components/charts/types";
>
> export function revisionChartSeries(data: Revisions): ChartSeries[];          // [first release, today's data]
> export function largestRevisions(data: Revisions, n?: number): RevisionPointOut[]; // default n = 5
> export function signalLabel(signal: TechnicalSignal): { label: string; tone: "neutral" | "warn" | "accent" };
> export function formatSigned(value: number | null | undefined, digits?: number): string; // default 2
> ```
>
> ## Rules
> 1. Only points with `first_release === true` are used anywhere (back-filled history is excluded).
> 2. `revisionChartSeries`: points sorted by period (labels sort lexicographically, "2020-Q2" < "2022-Q1");
>    series 1: id `${country}-${indicator.id}-first-release`, name "First release", values `first_value`;
>    series 2: id `${country}-${indicator.id}-latest`, name "Today's data", values `latest_value` (null stays null).
>    Both: `unit` = `data.indicator.unit`, `source` = `ALFRED · ${series.dataset}`, `citation` =
>    `ALFRED (Federal Reserve Bank of St. Louis), ${dataset}; ${vintages} vintages ${first_vintage} to ${last_vintage}; retrieved ${retrieved_at.slice(0, 10)}`.
> 3. `largestRevisions`: points with a non-null `revision`, sorted by `Math.abs(revision)` descending, ties by
>    period ascending; the first `n`.
> 4. `signalLabel`: both flags → "Confirmed by today's data" / "neutral"; only `as_first_known` → "Revised away" /
>    "warn"; only `in_latest_data` → "Only visible in today's data" / "accent".
> 5. `formatSigned`: `Intl.NumberFormat("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits,
>    signDisplay: "exceptZero" })`; non-finite or null/undefined → "N/A". Cache formatters per `digits` in a Map.
> 6. TypeScript strict with `noUncheckedIndexedAccess`; no `any`, no `!`; never mutate `data` (copy before sorting).
>
> Output only the file, in ONE fenced code block (three backticks, language ts) — do not nest fences.
>
> # Output file
>
> `apps/web/src/lib/revisions.ts`
>
> # Context files
>
> ## `apps/web/src/lib/revisions.test.ts`
>
> ```ts
> import { describe, expect, it } from "vitest";
>
> import { formatSigned, largestRevisions, revisionChartSeries, signalLabel } from "@/lib/revisions";
> import { REVISIONS_FIXTURE as data } from "@/lib/revisions.fixture";
>
> describe("revisionChartSeries", () => {
>   it("draws first releases and today's values for genuine first releases only, in period order", () => {
>     const [first, latest] = revisionChartSeries(data);
>     expect(first?.name).toBe("First release");
>     expect(latest?.name).toBe("Today's data");
>     // 1990-Q1 is back-filled history (first_release false) and is left out of both lines
>     expect(first?.points).toEqual([
>       { period: "2020-Q2", value: -9.49 },
>       { period: "2022-Q1", value: -0.36 },
>       { period: "2022-Q2", value: -0.23 },
>       { period: "2022-Q3", value: 0.65 },
>     ]);
>     // a missing latest value stays a gap (null), it is not dropped or filled
>     expect(latest?.points.at(-1)).toEqual({ period: "2022-Q3", value: null });
>   });
>
>   it("carries ids, unit and an ALFRED citation", () => {
>     const [first, latest] = revisionChartSeries(data);
>     expect(first?.id).toBe("US-real_gdp_qoq-first-release");
>     expect(latest?.id).toBe("US-real_gdp_qoq-latest");
>     expect(first?.unit).toBe("%");
>     expect(first?.source).toBe("ALFRED · GDPC1");
>     expect(first?.citation).toBe(
>       "ALFRED (Federal Reserve Bank of St. Louis), GDPC1; 420 vintages 1991-12-04 to 2026-10-29; retrieved 2026-11-12",
>     );
>   });
>
>   it("does not mutate the response", () => {
>     const before = JSON.stringify(data);
>     revisionChartSeries(data);
>     largestRevisions(data);
>     expect(JSON.stringify(data)).toBe(before);
>   });
> });
>
> describe("largestRevisions", () => {
>   it("ranks genuine first releases by absolute revision, skipping missing revisions", () => {
>     expect(largestRevisions(data, 2).map((p) => p.period)).toEqual(["2020-Q2", "2022-Q2"]);
>     expect(largestRevisions(data).map((p) => p.period)).toEqual(["2020-Q2", "2022-Q2", "2022-Q1"]);
>   });
>
>   it("breaks ties by period", () => {
>     const base = data.points[1];
>     if (!base) throw new Error("fixture");
>     const tied = {
>       ...data,
>       points: [
>         { ...base, period: "2021-Q2", revision: -0.5 },
>         { ...base, period: "2021-Q1", revision: 0.5 },
>       ],
>     };
>     expect(largestRevisions(tied).map((p) => p.period)).toEqual(["2021-Q1", "2021-Q2"]);
>   });
> });
>
> describe("signalLabel", () => {
>   it("names the three cases in words", () => {
>     const [both, then, now] = data.technical_signals;
>     if (!both || !then || !now) throw new Error("fixture");
>     expect(signalLabel(both)).toEqual({ label: "Confirmed by today's data", tone: "neutral" });
>     expect(signalLabel(then)).toEqual({ label: "Revised away", tone: "warn" });
>     expect(signalLabel(now)).toEqual({ label: "Only visible in today's data", tone: "accent" });
>   });
> });
>
> describe("formatSigned", () => {
>   it("always shows the sign and two decimals; N/A for missing", () => {
>     expect(formatSigned(0.137)).toBe("+0.14");
>     expect(formatSigned(-0.23)).toBe("-0.23");
>     expect(formatSigned(0)).toBe("0.00");
>     expect(formatSigned(null)).toBe("N/A");
>     expect(formatSigned(Number.NaN)).toBe("N/A");
>     expect(formatSigned(1.2345, 3)).toBe("+1.235");
>   });
> });
>
> ```
>
> ## `apps/web/src/lib/revisions.fixture.ts`
>
> ```ts
> import t
> …(truncated)
