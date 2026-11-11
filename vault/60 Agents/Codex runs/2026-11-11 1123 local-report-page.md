---
type: codex-run
name: local-report-page
date: 2026-11-11
time: "11:23"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-report-page

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 11:23. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```tsx
> "use client";
>
> import { Braces, FileText, Sheet } from "lucide-react";
> import { useState } from "react";
>
> import { CountryRequired } from "@/components/views/country-required";
> import { Badge } from "@/components/ui/badge";
> import { Button } from "@/components/ui/button";
> import { Card, CardBody, CardHeader } from "@/components/ui/card";
> import { PageHeader } from "@/components/ui/page-header";
> import { ErrorState, Notice } from "@/components/ui/states";
> import { formatAsOf } from "@/lib/as-of";
> import { useAppContext } from "@/lib/context";
> import { downloadReport, type ReportFormat } from "@/lib/reports";
> import { useCountries } from "@/lib/queries";
>
> const REPORT_FORMATS: { format: ReportFormat; label: string; icon: typeof FileText }[] = [
>   { format: "pdf", label: "Download PDF", icon: FileText },
>   { format: "csv", label: "CSV (chart data)", icon: Sheet },
>   { format: "json", label: "JSON", icon: Braces },
> ];
>
> export function ReportsView() {
>   const { country, asOf } = useAppContext();
>   const countries = useCountries();
>   const selected = countries.data?.items.find((c) => c.iso2 === country);
>
>   const [busyFormat, setBusyFormat] = useState<ReportFormat | null>(null);
>   const [savedFilename, setSavedFilename] = useState<string | null>(null);
>   const [error, setError] = useState<unknown>(null);
>   const [lastFormat, setLastFormat] = useState<ReportFormat>("pdf");
>
>   async function run(format: ReportFormat) {
>     if (!selected) return;
>     setBusyFormat(format);
>     setLastFormat(format);
>     setSavedFilename(null);
>     setError(null);
>     try {
>       const filename = await downloadReport({ country: selected.iso2, asOf, format });
>       setSavedFilename(filename);
>     } catch (err) {
>       setError(err);
>     } finally {
>       setBusyFormat(null);
>     }
>   }
>
>   return (
>     <>
>       <PageHeader
>         eyebrow="Platform"
>         title="Report builder"
>         description="Download a dated report for the selected country: key indicators, charts, model estimates, forecasts, sources and limitations — built only from stored data."
>         meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
>       />
>       {!selected ? (
>         <CountryRequired purpose="Reports are generated per country." />
>       ) : (
>         <div className="space-y-4">
>           <Card>
>             <CardHeader
>               title="Download"
>               description={`${selected.name} · ${asOf ? `as of ${asOf}` : "latest stored data"}`}
>             />
>             <CardBody className="space-y-4">
>               <div className="flex flex-wrap gap-2">
>                 {REPORT_FORMATS.map(({ format, label, icon: Icon }) => (
>                   <Button
>                     key={format}
>                     variant={format === "pdf" ? "primary" : "default"}
>                     disabled={busyFormat !== null}
>                     onClick={() => void run(format)}
>                   >
>                     <Icon className="size-4" aria-hidden />
>                     {busyFormat === format ? "Generating…" : label}
>                   </Button>
>                 ))}
>               </div>
>               {savedFilename ? (
>                 <p role="status" className="text-sm text-fg-muted">
>                   Saved {savedFilename}
>                 </p>
>               ) : null}
>               {error ? <ErrorState error={error} onRetry={() => void run(lastFormat)} /> : null}
>             </CardBody>
>           </Card>
>
>           <Card>
>             <CardHeader title="What the report contains" />
>             <CardBody>
>               <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-fg-muted">
>                 <li>Key indicators with source flags and staleness.</li>
>                 <li>
>                   Charts of GDP growth (technical recessions shaded), inflation, unemployment and the
>                   policy rate for the last 10 years before the cut-off.
>                 </li>
>                 <li>
>                   Technical-recession estimates for 2 and 4 quarters with their held-out track record
>                   (or why there is none).
>                 </li>
>                 <li>
>                   Ridge-AR forecasts four quarters ahead with 80 % intervals and measured coverage.
>                 </li>
>                 <li>
>                   Methodology, limitations, numbered sources with request URLs and retrieval times.
>                 </li>
>                 <li>Disclaimer.</li>
>               </ul>
>             </CardBody>
>           </Card>
>
>           <Notice>
>             Reports use latest revised data. With an as-of quarter, only periods ending by its cut-off
>             are included; publication lags are not applied to the key indicators.
>           </Notice>
>         </div>
>       )}
>     </>
>   );
> }
> ```
>
> - Followed `forecasts-view.tsx` structure: `useAppContext` + `useCountries`, `CountryRequired` guard, `PageHeader` with `Badge` meta.
> - Single `busyFormat` state drives the "Generating…" label and disables all three buttons; `lastFormat` enables retry.
> - `downloadReport` returns the filename, shown in a `role="status"` line; errors render `ErrorState` with retry.
> - Used `variant="default"` for the non-PDF buttons (only `primary` was specified for PDF); adjust if the design system expects another variant name.
> - Icons imported from `lucide-react` with `aria-hidden`; no `any`, no extra libraries.

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: build the Report builder page (`/reports`) in the Next.js app.
>
> ## Files
> - CREATE `apps/web/src/components/views/reports-view.tsx` — the only file you write.
>   (`apps/web/src/app/reports/page.tsx` already renders `<ReportsView />` inside `<Suspense>`.)
> - CONTEXT (provided below, do not change): `apps/web/src/lib/reports.ts` (use `downloadReport`, `ReportFormat`),
>   `apps/web/src/components/views/forecasts-view.tsx` (follow its structure and imports),
>   `apps/web/src/lib/context.ts` (`useAppContext`), `apps/web/src/lib/queries.ts` (`useCountries`).
> Touch no other file.
>
> ## reports-view.tsx (`"use client"`, export `function ReportsView()`)
> 1. `PageHeader` eyebrow "Platform", title "Report builder", description
>    "Download a dated report for the selected country: key indicators, charts, model estimates, forecasts, sources and limitations — built only from stored data.",
>    meta `<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>` (`formatAsOf` from `@/lib/as-of`).
> 2. No country selected → `<CountryRequired purpose="Reports are generated per country." />`.
> 3. Otherwise a `Card` "Download" with `CardHeader` description
>    `{country name} · {asOf ? `as of ${asOf}` : "latest stored data"}` and three `Button`s:
>    "Download PDF" (`variant="primary"`), "CSV (chart data)" and "JSON". Icons from lucide-react:
>    `FileText`, `Sheet`, `Braces` with `aria-hidden`.
>    - Clicking calls `downloadReport({ country, asOf, format })`.
>    - While a download runs: that button shows "Generating…", all three are `disabled`.
>    - On success: a polite status line (`role="status"`) "Saved {filename}".
>    - On error: `<ErrorState error={error} onRetry={() => run(lastFormat)} />` (from `@/components/ui/states`).
>    Keep the state in `useState`; no other libraries.
> 4. A second `Card` "What the report contains" with a plain list (no fake data):
>    Key indicators with source flags and staleness; charts of GDP growth (technical recessions shaded),
>    inflation, unemployment and the policy rate (last 10 years before the cut-off); technical-recession
>    estimates for 2 and 4 quarters with their held-out track record (or why there is none); ridge-AR
>    forecasts four quarters ahead with 80 % intervals and measured coverage; methodology, limitations,
>    numbered sources with request URLs and retrieval times; disclaimer.
> 5. A `Notice` (from `@/components/ui/states`): "Reports use latest revised data. With an as-of quarter,
>    only periods ending by its cut-off are included; publication lags are not applied to the key indicators."
> 6. Accessible: buttons have visible text; no colour-only meaning; no `any`.
>
> ## Checks
> TypeScript strict, ESLint clean. The lead runs `pnpm typecheck`, `pnpm lint` and checks the page in a browser.
>
> # Output file
>
> `apps/web/src/components/views/reports-view.tsx`
>
> # Context files
>
> ## `apps/web/src/lib/reports.ts`
>
> ```ts
> import type { ApiErrorResponse } from "@macropulse/shared-types";
>
> import { ApiError, UNREACHABLE_MESSAGE } from "@/lib/api";
> import { downloadDataUrl } from "@/lib/export";
>
> export type ReportFormat = "pdf" | "csv" | "json";
>
> export interface ReportRequest {
>   country: string;
>   asOf: string | null;
>   format: ReportFormat;
> }
>
> /** `attachment; filename="macropulse-report-de-latest-20261110.pdf"` → the filename, if safe. */
> export function filenameFromDisposition(header: string | null, fallback: string): string {
>   const match = /filename="([A-Za-z0-9._-]+)"/.exec(header ?? "");
>   return match?.[1] ?? fallback;
> }
>
> function isErrorBody(value: unknown): value is ApiErrorResponse {
>   return typeof value === "object" && value !== null && "error" in value;
> }
>
> /** POST /api/reports/generate and return the file; errors become ApiError (with the API's code). */
> export async function fetchReport(
>   { country, asOf, format }: ReportRequest,
>   fetcher: typeof fetch = fetch,
> ): Promise<{ blob: Blob; filename: string }> {
>   let response: Response;
>   try {
>     response = await fetcher("/api/reports/generate", {
>       method: "POST",
>       headers: { "Content-Type": "application/json" },
>       body: JSON.stringify({ country, format, ...(asOf ? { as_of: asOf } : {}) }),
>     });
>   } catch {
>     throw new ApiError("api_unreachable", UNREACHABLE_MESSAGE, 0);
>   }
>   if (!response.ok) {
>     const body: unknown = await response.json().catch(() => null);
>     if (isErrorBody(body)) {
>       throw new ApiError(body.error.code, body.error.message, response.status, body.error.request_id ?? null);
>     }
>     throw response.status >= 500
>       ? new ApiError("api_unreachable", UNREACHABLE_MESSAGE, response.status)
>       : new ApiError("http_error", `Request failed with status ${response.status}.`, response.status);
>   }
>   const fallback = `macropulse-report-${country.toLowerCase()}-${asOf ?? "latest"}.${format}`;
>   return { blob: await response.blob(), filename: filenameFromDisposition(response.headers.get("Content-Disposition"), fallback) };
> }
>
> /** Generate and save a report in the browser. */
> export async function downloadReport(request: ReportRequest): Promise<string> {
>   const { blob, filename } = await fetchReport(request);
>   const url = URL.createObjectURL(blob);
>   try {
>     downloadDataUrl(filename, url);
>   } finally {
>     window.setTimeout(() => URL.revokeObjectURL(url), 1000);
>   }
>   return filename;
> }
>
> ```
>
> ## `apps/web/src/components/views/forecasts-view.tsx`
>
> ```tsx
> "use client";
>
> import * as Select from "@radix-ui/react-select";
> import { ChartLine, Check, ChevronDown } from "lucide-react";
> import { useRef, useState } from "react";
>
> import type { ForecastModel, ForecastResponse } from "@macropulse/shared-types";
>
> import { ChartFrame } from "@/components/charts/chart-frame";
> import { ForecastChart, type ForecastChartHandle } from "@/components/charts/forecast-chart";
> import { ProvenanceDetails } from "@/components/data/provenance";
> import { CountryRequired } from "@/components/views/country-required";
> import { Badge } from "@/components/ui/badge";
> import { Button } from "@/components/ui/bu
> …(truncated)
