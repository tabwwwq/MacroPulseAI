Task: write the React card of the Crisis time machine that compares the walk-forward estimate on
today's revised US data with the SAME fold model scored on the figures as first published (ALFRED).

## Files
- CREATE `apps/web/src/components/model/vintage-replay-card.tsx` — the only file you write.
- CONTEXT (provided below, do not change): `apps/web/src/components/model/vintage-replay-card.test.tsx`
  (the specification — read every assertion, including exact strings), `apps/web/src/lib/vintage-replay.fixture.ts`
  (the API response shape), `apps/web/src/lib/risk.ts` (`BANDS`, `formatProbability`),
  `apps/web/src/components/data/revisions-card.tsx` (code and styling conventions to copy),
  `apps/web/src/components/ui/states.tsx`, `apps/web/src/components/ui/card.tsx`.

## Exports (exactly these three)
    export function formatShift(revised: number, vintage: number | null): { text: string; words: string } | null;
    export function VintageReplayDetails({ data }: { data: VintageReplay }): JSX.Element;
    export function VintageReplayCard({ iso2, horizon, asOf }: { iso2: string; horizon: 2 | 4; asOf: string }): JSX.Element;

Imports: `import type { VintageReplay } from "@macropulse/shared-types";`, `useVintageReplay` from
`@/lib/queries` (signature `useVintageReplay(iso2, horizon, asOf)`, a TanStack `useQuery` result), `ApiError`
from `@/lib/api` (has `.status` and `.message`), `Badge`, `Card`, `CardBody`, `CardHeader`, `Skeleton`,
`EmptyState`, `ErrorState`, `Notice` from `@/components/ui/...` as in revisions-card.tsx, `cn` from `@/lib/cn`,
`History` from `lucide-react`. First line: `"use client";`.

## formatShift
`pp = (vintage - revised) * 100`, rounded to ONE decimal. `null` vintage → `null`. If the rounded value is 0
→ `{ text: "0.0 pp", words: "No change" }`. Positive → `"+19.5 pp"`, "Higher with the figures as first
published"; negative → `"-3.2 pp"` (ASCII hyphen), "Lower with the figures as first published".

## VintageReplayDetails (pure, no hooks), top to bottom inside `<div className="space-y-4">`
1. A grid `grid gap-2 sm:grid-cols-3` of three stat boxes (style of `Stat` in revisions-card.tsx).
   - Box 1: `<div role="group" aria-label="Today's revised data">` — label text "Today's revised data",
     value `formatProbability(data.revised_probability)`, hint "stored walk-forward estimate".
   - Box 2: `<div role="group" aria-label="As first published">` — label "As first published", value
     `formatProbability(data.vintage_probability)` (gives "N/A" for null) and, when `data.vintage_band` is set,
     a `<Badge tone={BANDS[band]?.tone ?? "neutral"}>` with `BANDS[band]?.label ?? band`.
   - Box 3 only when `formatShift(...)` is not null: label "Shift", value = `shift.text`, hint = `shift.words`.
2. When `data.available` is false: `<Notice>{data.reason}</Notice>` and nothing else from 3-4 below.
3. When available: a horizontally scrollable wrapper exactly like KnownInputs in the history page
   (`<div className="relative -mx-5 overflow-x-auto px-5" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">`)
   with `<table className="w-full min-w-[560px] text-left text-xs tabular">` and
   `<caption className="sr-only">Inputs: today's data versus first published</caption>`.
   Header columns: Input | Today's data | First published | Difference. One row per input with
   `from_vintage === true`, in the given order: `<th scope="row">` = label; "Today's data" cell = value with 2
   decimals (`toFixed(2)`) in one `<span>` and the period in a separate small `<span>` (omit when null);
   "First published" the same with `vintage_value` / `vintage_period`; "Difference" = signed 2 decimals in one
   `<span>` ("+1.23", "-0.40", and "0.00" when it rounds to zero — never "-0.00" or "+0.00"), plus
   `<Badge tone="warn">revised</Badge>` when `Math.abs(difference) >= 0.005`.
4. When available: `<p>` "Not revised, identical in both: " + labels of the inputs with `from_vintage === false`
   joined by ", " + "." (omit the paragraph when there are none).
5. Always: `<p className="text-xs leading-relaxed text-fg-subtle">{data.note}</p>` and a mono line
   `Fold ${data.fold_year ?? "—"} · vintage of ${data.vintage_date} · archive from ${data.archive_start}`.

## VintageReplayCard
`const q = useVintageReplay(iso2, horizon, asOf);` Wrap everything in `<Card>` with
`<CardHeader title="With the figures as first published" description="Same walk-forward fold model · US GDP, CPI and unemployment from the ALFRED vintage of the cut-off date" action={<Badge tone="accent">ALFRED vintage</Badge>} />`
and a `<CardBody>`. In the body: pending → `<Skeleton className="h-48 rounded-xl" />`; error that is an
`ApiError` with status 404, 422 or 503 → `<EmptyState icon={<History className="size-6" aria-hidden />} title="First-release comparison unavailable">{error.message}</EmptyState>`;
other error → `<ErrorState error={q.error} onRetry={() => void q.refetch()} />`; data → `<VintageReplayDetails data={q.data} />`.
Set `aria-busy={q.isFetching}` on the Card.

## Rules
- TypeScript strict, no `any`, no new dependencies, Tailwind classes only (tokens: text-fg, text-fg-muted,
  text-fg-subtle, border-line, bg-canvas/50, font-mono, tabular). Colour never carries meaning alone.
- Output only the file, in ONE fenced code block (three backticks, language tsx) — do not nest fences.
