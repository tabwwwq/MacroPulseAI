---
type: codex-run
name: local-vintage-replay-card
date: 2026-11-12
time: "14:59"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-vintage-replay-card

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-12 14:59. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```tsx
> "use client";
>
> import { History } from "lucide-react";
>
> import type { VintageReplay } from "@macropulse/shared-types";
>
> import { Badge } from "@/components/ui/badge";
> import { Card, CardBody, CardHeader } from "@/components/ui/card";
> import { Skeleton } from "@/components/ui/skeleton";
> import { EmptyState, ErrorState, Notice } from "@/components/ui/states";
> import { ApiError } from "@/lib/api";
> import { useVintageReplay } from "@/lib/queries";
> import { BANDS, formatProbability } from "@/lib/risk";
> import { cn } from "@/lib/cn";
>
> /**
>  * Signed shift between the walk-forward estimate on today's revised data and the same fold model
>  * scored on the figures as first published (ALFRED). `null` vintage → `null`.
>  */
> export function formatShift(revised: number, vintage: number | null): { text: string; words: string } | null {
>   if (vintage === null) return null;
>   const pp = Math.round((vintage - revised) * 1000) / 10;
>   if (pp === 0) return { text: "0.0 pp", words: "No change" };
>   const text = `${pp > 0 ? "+" : ""}${pp.toFixed(1)} pp`;
>   return {
>     text,
>     words: pp > 0 ? "Higher with the figures as first published" : "Lower with the figures as first published",
>   };
> }
>
> function Stat({ label, value, hint, children }: { label: string; value: string; hint?: string; children?: React.ReactNode }) {
>   return (
>     <div className="rounded-xl border border-line bg-canvas/50 px-3 py-2.5">
>       <p className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-fg-subtle">{label}</p>
>       <p className="tabular mt-1 font-mono text-lg font-semibold text-fg">{value}</p>
>       {hint ? <p className="mt-0.5 text-[11px] text-fg-subtle">{hint}</p> : null}
>       {children}
>     </div>
>   );
> }
>
> /** Signed 2-decimal difference, never "-0.00" or "+0.00". */
> function signedDiff(v: number): string {
>   const r = Math.round(v * 100) / 100;
>   if (r === 0) return "0.00";
>   return `${r > 0 ? "+" : ""}${r.toFixed(2)}`;
> }
>
> /** One input value: 2 decimals in one span, the period in a separate small span (omitted when null). */
> function ValueCell({ value, period }: { value: number; period: string | null }) {
>   return (
>     <span className="tabular font-mono text-fg">
>       {value.toFixed(2)}
>       {period ? <span className="ml-1 text-[10px] text-fg-subtle">{period}</span> : null}
>     </span>
>   );
> }
>
> /** Pure details: both estimates, the shift, and the rebuilt inputs compared against today. */
> export function VintageReplayDetails({ data }: { data: VintageReplay }): JSX.Element {
>   const shift = formatShift(data.revised_probability, data.vintage_probability);
>   const fromVintage = data.inputs.filter((i) => i.from_vintage);
>   const notRevised = data.inputs.filter((i) => !i.from_vintage);
>
>   return (
>     <div className="space-y-4">
>       <div className="grid gap-2 sm:grid-cols-3">
>         <div role="group" aria-label="Today's revised data">
>           <Stat label="Today's revised data" value={formatProbability(data.revised_probability)} hint="stored walk-forward estimate" />
>         </div>
>         <div role="group" aria-label="As first published">
>           <Stat label="As first published" value={formatProbability(data.vintage_probability)}>
>             {data.vintage_band ? (
>               <div className="mt-1.5">
>                 <Badge tone={BANDS[data.vintage_band]?.tone ?? "neutral"}>{BANDS[data.vintage_band]?.label ?? data.vintage_band}</Badge>
>               </div>
>             ) : null}
>           </Stat>
>         </div>
>         {shift ? (
>           <Stat label="Shift" value={shift.text} hint={shift.words} />
>         ) : null}
>       </div>
>
>       {!data.available ? (
>         <Notice>{data.reason}</Notice>
>       ) : (
>         <>
>           <div
>             className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent"
>             tabIndex={0}
>             role="region"
>             aria-label="Table, scrolls horizontally"
>           >
>             <table className="w-full min-w-[560px] text-left text-xs tabular">
>               <caption className="sr-only">Inputs: today's data versus first published</caption>
>               <thead className="text-fg-subtle">
>                 <tr>
>                   <th scope="col" className="py-2 pr-4 font-medium">Input</th>
>                   <th scope="col" className="py-2 pr-4 font-medium">Today's data</th>
>                   <th scope="col" className="py-2 pr-4 font-medium">First published</th>
>                   <th scope="col" className="py-2 font-medium">Difference</th>
>                 </tr>
>               </thead>
>               <tbody className="font-mono text-xs">
>                 {fromVintage.map((i) => (
>                   <tr key={i.feature} className="border-t border-line/60">
>                     <th scope="row" className="py-2 pr-4 font-normal text-fg">{i.label}</th>
>                     <td className="py-2 pr-4">
>                       <ValueCell value={i.revised_value} period={i.revised_period} />
>                     </td>
>                     <td className="py-2 pr-4">
>                       <ValueCell value={i.vintage_value} period={i.vintage_period} />
>                     </td>
>                     <td className="py-2">
>                       <span className="tabular font-mono text-fg">{signedDiff(i.difference)}</span>
>                       {Math.abs(i.difference) >= 0.005 ? (
>                         <Badge tone="warn" className="ml-2">revised</Badge>
>                       ) : null}
>                     </td>
>                   </tr>
>                 ))}
>               </tbody>
>             </table>
>           </div>
>
>           {notRevised.length ? (
>             <p className="text-xs leading-relaxed text-fg-muted">
>               Not revised, identical in both: {notRevised.map((i) => i.label).join(", ")}.
>             </p>
>           ) : null}
>         </>
>       )}
>
>       <p className="text-xs leading-relaxed text-fg-subtle">{data.note}</p>
>       <p className="font-mono text-[11px] text-fg-subtle">
>         Fold {data.fold_year ?? "—"} · vintage of {data.v
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the React card of the Crisis time machine that compares the walk-forward estimate on
> today's revised US data with the SAME fold model scored on the figures as first published (ALFRED).
>
> ## Files
> - CREATE `apps/web/src/components/model/vintage-replay-card.tsx` — the only file you write.
> - CONTEXT (provided below, do not change): `apps/web/src/components/model/vintage-replay-card.test.tsx`
>   (the specification — read every assertion, including exact strings), `apps/web/src/lib/vintage-replay.fixture.ts`
>   (the API response shape), `apps/web/src/lib/risk.ts` (`BANDS`, `formatProbability`),
>   `apps/web/src/components/data/revisions-card.tsx` (code and styling conventions to copy),
>   `apps/web/src/components/ui/states.tsx`, `apps/web/src/components/ui/card.tsx`.
>
> ## Exports (exactly these three)
>     export function formatShift(revised: number, vintage: number | null): { text: string; words: string } | null;
>     export function VintageReplayDetails({ data }: { data: VintageReplay }): JSX.Element;
>     export function VintageReplayCard({ iso2, horizon, asOf }: { iso2: string; horizon: 2 | 4; asOf: string }): JSX.Element;
>
> Imports: `import type { VintageReplay } from "@macropulse/shared-types";`, `useVintageReplay` from
> `@/lib/queries` (signature `useVintageReplay(iso2, horizon, asOf)`, a TanStack `useQuery` result), `ApiError`
> from `@/lib/api` (has `.status` and `.message`), `Badge`, `Card`, `CardBody`, `CardHeader`, `Skeleton`,
> `EmptyState`, `ErrorState`, `Notice` from `@/components/ui/...` as in revisions-card.tsx, `cn` from `@/lib/cn`,
> `History` from `lucide-react`. First line: `"use client";`.
>
> ## formatShift
> `pp = (vintage - revised) * 100`, rounded to ONE decimal. `null` vintage → `null`. If the rounded value is 0
> → `{ text: "0.0 pp", words: "No change" }`. Positive → `"+19.5 pp"`, "Higher with the figures as first
> published"; negative → `"-3.2 pp"` (ASCII hyphen), "Lower with the figures as first published".
>
> ## VintageReplayDetails (pure, no hooks), top to bottom inside `<div className="space-y-4">`
> 1. A grid `grid gap-2 sm:grid-cols-3` of three stat boxes (style of `Stat` in revisions-card.tsx).
>    - Box 1: `<div role="group" aria-label="Today's revised data">` — label text "Today's revised data",
>      value `formatProbability(data.revised_probability)`, hint "stored walk-forward estimate".
>    - Box 2: `<div role="group" aria-label="As first published">` — label "As first published", value
>      `formatProbability(data.vintage_probability)` (gives "N/A" for null) and, when `data.vintage_band` is set,
>      a `<Badge tone={BANDS[band]?.tone ?? "neutral"}>` with `BANDS[band]?.label ?? band`.
>    - Box 3 only when `formatShift(...)` is not null: label "Shift", value = `shift.text`, hint = `shift.words`.
> 2. When `data.available` is false: `<Notice>{data.reason}</Notice>` and nothing else from 3-4 below.
> 3. When available: a horizontally scrollable wrapper exactly like KnownInputs in the history page
>    (`<div className="relative -mx-5 overflow-x-auto px-5" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">`)
>    with `<table className="w-full min-w-[560px] text-left text-xs tabular">` and
>    `<caption className="sr-only">Inputs: today's data versus first published</caption>`.
>    Header columns: Input | Today's data | First published | Difference. One row per input with
>    `from_vintage === true`, in the given order: `<th scope="row">` = label; "Today's data" cell = value with 2
>    decimals (`toFixed(2)`) in one `<span>` and the period in a separate small `<span>` (omit when null);
>    "First published" the same with `vintage_value` / `vintage_period`; "Difference" = signed 2 decimals in one
>    `<span>` ("+1.23", "-0.40", and "0.00" when it rounds to zero — never "-0.00" or "+0.00"), plus
>    `<Badge tone="warn">revised</Badge>` when `Math.abs(difference) >= 0.005`.
> 4. When available: `<p>` "Not revised, identical in both: " + labels of the inputs with `from_vintage === false`
>    joined by ", " + "." (omit the paragraph when there are none).
> 5. Always: `<p className="text-xs leading-relaxed text-fg-subtle">{data.note}</p>` and a mono line
>    `Fold ${data.fold_year ?? "—"} · vintage of ${data.vintage_date} · archive from ${data.archive_start}`.
>
> ## VintageReplayCard
> `const q = useVintageReplay(iso2, horizon, asOf);` Wrap everything in `<Card>` with
> `<CardHeader title="With the figures as first published" description="Same walk-forward fold model · US GDP, CPI and unemployment from the ALFRED vintage of the cut-off date" action={<Badge tone="accent">ALFRED vintage</Badge>} />`
> and a `<CardBody>`. In the body: pending → `<Skeleton className="h-48 rounded-xl" />`; error that is an
> `ApiError` with status 404, 422 or 503 → `<EmptyState icon={<History className="size-6" aria-hidden />} title="First-release comparison unavailable">{error.message}</EmptyState>`;
> other error → `<ErrorState error={q.error} onRetry={() => void q.refetch()} />`; data → `<VintageReplayDetails data={q.data} />`.
> Set `aria-busy={q.isFetching}` on the Card.
>
> ## Rules
> - TypeScript strict, no `any`, no new dependencies, Tailwind classes only (tokens:*** text-fg-muted,
>   text-fg-subtle, border-line, bg-canvas/50, font-mono, tabular). Colour never carries meaning alone.
> - Output only the file, in ONE fenced code block (three backticks, language tsx) — do not nest fences.
>
> # Output file
>
> `apps/web/src/components/model/vintage-replay-card.tsx`
>
> # Context files
>
> ## `apps/web/src/components/model/vintage-replay-card.test.tsx`
>
> ```tsx
> import { render, screen, within } from "@testing-library/react";
> import { describe, expect, it } from "vitest";
>
> import { formatShift, VintageReplayDetails } from "@/components/model/vintage-replay-card";
> import { VINTAGE_REPLAY_FIXTURE as data, VINTAGE_REPLAY_UNAVAILABLE as unavailable } from "@/lib/vintage-replay.fixture";
>
> describe("formatShift", () => {
>   it("states the change in percentage points and in words", () => {
>     expect(formatShift(0.12, 0.315)).toEqual({
> …(truncated)
