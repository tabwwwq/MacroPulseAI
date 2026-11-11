Task: build the Report builder page (`/reports`) in the Next.js app.

## Files
- CREATE `apps/web/src/components/views/reports-view.tsx` — the only file you write.
  (`apps/web/src/app/reports/page.tsx` already renders `<ReportsView />` inside `<Suspense>`.)
- CONTEXT (provided below, do not change): `apps/web/src/lib/reports.ts` (use `downloadReport`, `ReportFormat`),
  `apps/web/src/components/views/forecasts-view.tsx` (follow its structure and imports),
  `apps/web/src/lib/context.ts` (`useAppContext`), `apps/web/src/lib/queries.ts` (`useCountries`).
Touch no other file.

## reports-view.tsx (`"use client"`, export `function ReportsView()`)
1. `PageHeader` eyebrow "Platform", title "Report builder", description
   "Download a dated report for the selected country: key indicators, charts, model estimates, forecasts, sources and limitations — built only from stored data.",
   meta `<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>` (`formatAsOf` from `@/lib/as-of`).
2. No country selected → `<CountryRequired purpose="Reports are generated per country." />`.
3. Otherwise a `Card` "Download" with `CardHeader` description
   `{country name} · {asOf ? `as of ${asOf}` : "latest stored data"}` and three `Button`s:
   "Download PDF" (`variant="primary"`), "CSV (chart data)" and "JSON". Icons from lucide-react:
   `FileText`, `Sheet`, `Braces` with `aria-hidden`.
   - Clicking calls `downloadReport({ country, asOf, format })`.
   - While a download runs: that button shows "Generating…", all three are `disabled`.
   - On success: a polite status line (`role="status"`) "Saved {filename}".
   - On error: `<ErrorState error={error} onRetry={() => run(lastFormat)} />` (from `@/components/ui/states`).
   Keep the state in `useState`; no other libraries.
4. A second `Card` "What the report contains" with a plain list (no fake data):
   Key indicators with source flags and staleness; charts of GDP growth (technical recessions shaded),
   inflation, unemployment and the policy rate (last 10 years before the cut-off); technical-recession
   estimates for 2 and 4 quarters with their held-out track record (or why there is none); ridge-AR
   forecasts four quarters ahead with 80 % intervals and measured coverage; methodology, limitations,
   numbered sources with request URLs and retrieval times; disclaimer.
5. A `Notice` (from `@/components/ui/states`): "Reports use latest revised data. With an as-of quarter,
   only periods ending by its cut-off are included; publication lags are not applied to the key indicators."
6. Accessible: buttons have visible text; no colour-only meaning; no `any`.

## Checks
TypeScript strict, ESLint clean. The lead runs `pnpm typecheck`, `pnpm lint` and checks the page in a browser.
