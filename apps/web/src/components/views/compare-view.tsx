"use client";

import { useQueries, type UseQueryResult } from "@tanstack/react-query";
import { TriangleExclamationPoint } from "lucide-react";

import type { CatalogEntry, IndicatorSeries } from "@macropulse/shared-types";

import { ChartFrame } from "@/components/charts/chart-frame";
import { isExpectedAbsence } from "@/components/data/indicator-chart";
import { RangeControl, useRange } from "@/components/data/range-control";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { cn } from "@/lib/cn";
import { useAppContext } from "@/lib/context";
import { formatDateTimeUtc } from "@/lib/format";
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { seriesQueryOptions, useCatalog, useCountries } from "@/lib/queries";
import { provenanceLabel, rangeBounds, spreadVsBaseline, toChartSeries } from "@/lib/series";

const MAX = 4;
const METRICS = [
  { value: "real_gdp_qoq", label: "GDP q/q" },
  { value: "real_gdp_yoy", label: "GDP y/y" },
  { value: "inflation_yoy", label: "Inflation" },
  { value: "unemployment_rate", label: "Unemployment" },
  { value: "gov_debt_gdp", label: "Debt" },
  { value: "policy_rate", label: "Policy rate" },
] as const;
type Metric = (typeof METRICS)[number]["value"];
const MODES = [
  { value: "level", label: "As published" },
  { value: "spread", label: "Spread vs first" },
] as const;
type Mode = (typeof MODES)[number]["value"];

export function parseSelection(raw: string | null, fallback: string | null): string[] {
  const list = (raw ?? "")
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter((s) => /^[A-Z]{2}$/.test(s));
  const unique = [...new Set(list)].slice(0, MAX);
  return unique.length > 0 ? unique : fallback ? [fallback] : [];
}

/** Stable across renders unless a query result changes (module-level `combine`). */
function combineSeries(results: UseQueryResult<IndicatorSeries>[]) {
  return {
    data: results.map((r) => r.data),
    errors: results.map((r) => r.error),
    pending: results.map((r) => r.isPending),
    refetchAll: () => results.forEach((r) => void r.refetch()),
  };
}

interface Row {
  iso2: string;
  entry: CatalogEntry | undefined;
  data: IndicatorSeries | undefined;
  error: unknown;
  pending: boolean;
}

/** Human-readable reasons why the selected series are not directly comparable. */
export function comparabilityWarnings(rows: Pick<Row, "iso2" | "entry">[]): string[] {
  const entries = rows.flatMap((r) => (r.entry ? [{ iso2: r.iso2, e: r.entry }] : []));
  const warnings: string[] = [];
  const datasets = new Set(entries.map(({ e }) => e.mapping.dataset).filter(Boolean));
  if (datasets.size > 1) {
    warnings.push(
      `Different source series (${[...datasets].join(", ")}): definitions, adjustment or transformation may differ.`,
    );
  }
  const frequencies = new Set(entries.map(({ e }) => e.mapping.native_frequency).filter(Boolean));
  if (frequencies.size > 1) {
    warnings.push(
      `Different native frequencies (${[...frequencies].join(", ")}): values are placed on a shared time axis but are not period-aligned.`,
    );
  }
  for (const { iso2, e } of entries) {
    if (e.mapping.scope_note) warnings.push(`${iso2}: ${e.mapping.scope_note}`);
  }
  const shared = entries.filter(({ e }) => e.mapping.scope_note.startsWith("Shared euro area"));
  if (shared.length > 1) {
    warnings.push(`${shared.map((s) => s.iso2).join(", ")} share one ECB rate — differences between them are zero by construction.`);
  }
  return [...new Set(warnings)];
}

export function CompareView() {
  const { country, asOf, params, setParam } = useAppContext();
  const countries = useCountries();
  const catalog = useCatalog(null);
  const [range] = useRange();
  const selected = parseSelection(params.get("countries"), country);
  const metricParam = params.get("metric");
  const metric: Metric = METRICS.some((m) => m.value === metricParam) ? (metricParam as Metric) : "real_gdp_qoq";
  const modeParam = params.get("mode");
  const bounds = rangeBounds(range, asOf);

  const { data: seriesData, errors, pending, refetchAll } = useQueries({
    queries: selected.map((iso2) => seriesQueryOptions({ country: iso2, indicator: metric, ...bounds })),
    combine: combineSeries,
  });

  const rows: Row[] = selected.map((iso2, i) => ({
    iso2,
    entry: catalog.data?.countries.find((c) => c.country === iso2)?.items.find((it) => it.indicator.id === metric),
    data: seriesData[i],
    error: errors[i],
    pending: pending[i] ?? true,
  }));
  const warnings = comparabilityWarnings(rows);
  const frequencies = new Set(rows.map((r) => r.entry?.mapping.native_frequency).filter(Boolean));
  const spreadAllowed = rows.filter((r) => r.data).length > 1 && frequencies.size <= 1;
  const mode: Mode = modeParam === "spread" && spreadAllowed ? "spread" : "level";

  // Legend uses the common indicator unit; native unit labels stay in the table below.
  const baseSeries = seriesData.flatMap((d, i) => (d ? [{ ...toChartSeries(d, selected[i]), unit: d.indicator.unit }] : []));
  const chartSeries = mode === "spread" ? spreadVsBaseline(baseSeries) : baseSeries;

  const unexpected = rows.find((r) => r.error && !isExpectedAbsence(r.error));
  const absent = rows.filter((r) => isExpectedAbsence(r.error));
  const loading = rows.some((r) => r.pending) && chartSeries.length === 0;
  const metricLabel = METRICS.find((m) => m.value === metric)?.label ?? metric;
  const baseline = rows.find((r) => r.data)?.iso2;

  function toggle(iso2: string) {
    const next = selected.includes(iso2) ? selected.filter((c) => c !== iso2) : [...selected, iso2].slice(0, MAX);
    setParam("countries", next.length ? next.join(",") : null);
  }

  return (
    <>
      <PageHeader
        eyebrow="Monitor"
        title="Compare countries"
        description="Up to four countries on the same indicator, from stored official series, with explicit warnings where definitions, frequency or scope are not comparable."
        meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
      />

      <Card className="mb-4">
        <CardBody className="flex flex-col gap-4 pt-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <fieldset>
              <legend className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">
                Countries · {selected.length}/{MAX}
              </legend>
              <div className="flex flex-wrap gap-2">
                {countries.isPending ? (
                  <Skeleton className="h-8 w-72" />
                ) : (
                  countries.data?.items.map((c) => {
                    const on = selected.includes(c.iso2);
                    const blocked = !on && selected.length >= MAX;
                    return (
                      <button
                        key={c.iso2}
                        type="button"
                        aria-pressed={on}
                        disabled={blocked}
                        title={blocked ? `At most ${MAX} countries` : undefined}
                        onClick={() => toggle(c.iso2)}
                        className={cn(
                          "inline-flex h-8 items-center gap-2 rounded-full border px-3 text-sm transition-colors disabled:opacity-40",
                          on ? "border-accent/40 bg-accent/10 text-fg" : "border-line-strong bg-surface-2 text-fg-muted hover:text-fg",
                        )}
                      >
                        <span className="font-mono text-xs">{c.iso2}</span>
                        {c.name}
                      </button>
                    );
                  })
                )}
              </div>
            </fieldset>
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Window</p>
              <RangeControl />
            </div>
          </div>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="min-w-0">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Indicator</p>
              <Segmented label="Indicator" options={[...METRICS]} value={metric} onChange={(v) => setParam("metric", v)} />
            </div>
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Normalisation</p>
              <Segmented
                label="Normalisation"
                options={[...MODES]}
                value={mode}
                onChange={(v) => setParam("mode", v === "level" ? null : v)}
              />
              {modeParam === "spread" && !spreadAllowed ? (
                <p className="mt-1.5 max-w-xs text-xs text-warn">
                  Spread needs two or more stored series with the same native frequency.
                </p>
              ) : null}
            </div>
          </div>
        </CardBody>
      </Card>

      {catalog.isError ? <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} className="mb-4" /> : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="min-w-0 xl:col-span-2">
          <WidgetBoundary label="Comparison chart">
            <ChartFrame
              title={`${metricLabel} · ${selected.join(", ") || "no countries selected"}${mode === "spread" && baseline ? ` · spread vs ${baseline}` : ""}`}
              description={
                mode === "spread"
                  ? `Difference to ${baseline} in percentage points, only on periods both countries published.`
                  : "Each country's stored series as published (or as derived by the documented transform)."
              }
              series={chartSeries}
              isLoading={loading}
              error={unexpected?.error}
              onRetry={refetchAll}
              emptyTitle={selected.length ? "Nothing to compare in this window" : "Select at least one country"}
              emptyMessage={
                selected.length
                  ? absent.length
                    ? absent.map((r) => `${r.iso2}: ${(r.error as Error).message}`).join(" ")
                    : "No stored observation falls inside the selected window and as-of cut-off."
                  : "Use the country chips above."
              }
              notes={
                absent.length ? (
                  <p className="mt-3 text-xs text-warn">
                    Not shown: {absent.map((r) => `${r.iso2} (${(r.error as Error).message})`).join("; ")}
                  </p>
                ) : null
              }
              allowKindToggle
              exportName={`macropulse-compare-${metric}-${selected.join("-").toLowerCase()}${mode === "spread" ? "-spread" : ""}`}
              height={320}
            />
          </WidgetBoundary>
        </div>
        <Card>
          <CardHeader title="Comparability" description="Derived from the verified source mappings." />
          <CardBody>
            {warnings.length ? (
              <ul className="space-y-2.5">
                {warnings.map((w) => (
                  <li key={w} className="flex gap-2 text-sm text-fg-muted">
                    <TriangleExclamationPoint className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
                    {w}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-fg-muted">
                {selected.length > 1 ? "Same source series, frequency and scope for all selected countries." : "Select two or more countries to check comparability."}
              </p>
            )}
          </CardBody>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader title="Per-country source and latest stored value" />
        <CardBody>
          <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
            <table className="w-full min-w-[760px] text-left text-sm">
              <caption className="sr-only">Source and latest stored value per selected country</caption>
              <thead>
                <tr className="border-b border-line text-xs text-fg-subtle">
                  <th scope="col" className="py-2 pr-4 font-medium">Country</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Source · dataset</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Status</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Latest in window</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Fetched</th>
                  <th scope="col" className="py-2 font-medium">Note</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ iso2, entry, data, error, pending }) => {
                  const last = data?.points.at(-1);
                  return (
                    <tr key={iso2} className="border-b border-line/60 align-top last:border-0">
                      <th scope="row" className="py-3 pr-4 font-mono text-fg">{iso2}</th>
                      <td className="py-3 pr-4 text-fg-muted">
                        {data ? provenanceLabel(data.provenance) : entry ? (sourceLabel(entry) ?? "—") : "…"}
                      </td>
                      <td className="py-3 pr-4">
                        {entry ? (
                          <Badge tone={MAPPING_STATUS[entry.mapping.status].tone} dashed={MAPPING_STATUS[entry.mapping.status].tone === "neutral"}>
                            {MAPPING_STATUS[entry.mapping.status].label}
                          </Badge>
                        ) : null}
                      </td>
                      <td className="tabular py-3 pr-4 font-mono text-xs text-fg">
                        {pending ? "…" : last ? `${last.value.toFixed(2)} ${data?.unit ?? ""} · ${last.period}` : "—"}
                      </td>
                      <td className="py-3 pr-4 text-xs text-fg-muted">{data ? formatDateTimeUtc(data.provenance.retrieved_at) : "—"}</td>
                      <td className="py-3 text-xs text-fg-muted">
                        {error ? (error as Error).message : data?.scope_note || (entry && !data ? availabilityReason(entry) : "")}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </>
  );
}
