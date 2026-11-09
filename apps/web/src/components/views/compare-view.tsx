"use client";

import { TriangleExclamationPoint } from "lucide-react";
import { useMemo } from "react";

import type { CatalogEntry } from "@macropulse/shared-types";

import { ChartFrame } from "@/components/charts/chart-frame";
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
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { useCatalog, useCountries } from "@/lib/queries";

const MAX = 4;
const METRICS = [
  { value: "real_gdp_qoq", label: "GDP q/q" },
  { value: "inflation_yoy", label: "Inflation" },
  { value: "unemployment_rate", label: "Unemployment" },
  { value: "gov_debt_gdp", label: "Debt" },
  { value: "policy_rate", label: "Policy rate" },
] as const;
type Metric = (typeof METRICS)[number]["value"];

function parseSelection(raw: string | null, fallback: string | null): string[] {
  const list = (raw ?? "")
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter((s) => /^[A-Z]{2}$/.test(s));
  const unique = [...new Set(list)].slice(0, MAX);
  return unique.length > 0 ? unique : fallback ? [fallback] : [];
}

/** Human-readable reasons why the selected series are not directly comparable. */
function comparabilityWarnings(rows: { iso2: string; entry: CatalogEntry | undefined }[]): string[] {
  const entries = rows.flatMap((r) => (r.entry ? [{ iso2: r.iso2, e: r.entry }] : []));
  const warnings: string[] = [];
  const datasets = new Set(entries.map(({ e }) => e.mapping.dataset).filter(Boolean));
  if (datasets.size > 1) {
    warnings.push(
      `Different source series (${[...datasets].join(", ")}): definitions, adjustment or transformation may differ.`,
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
  const selected = parseSelection(params.get("countries"), country);
  const metricParam = params.get("metric");
  const metric: Metric = METRICS.some((m) => m.value === metricParam) ? (metricParam as Metric) : "real_gdp_qoq";

  const rows = useMemo(
    () =>
      selected.map((iso2) => ({
        iso2,
        entry: catalog.data?.countries.find((c) => c.country === iso2)?.items.find((i) => i.indicator.id === metric),
      })),
    [catalog.data, metric, selected],
  );
  const warnings = comparabilityWarnings(rows);

  function toggle(iso2: string) {
    const next = selected.includes(iso2) ? selected.filter((c) => c !== iso2) : [...selected, iso2].slice(0, MAX);
    setParam("countries", next.length ? next.join(",") : null);
  }

  return (
    <>
      <PageHeader
        eyebrow="Monitor"
        title="Compare countries"
        description="Up to four countries on the same indicator, with explicit warnings where definitions, units or scope are not comparable."
        meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
      />

      <Card className="mb-4">
        <CardBody className="flex flex-col gap-4 pt-5 lg:flex-row lg:items-center lg:justify-between">
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
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Indicator</p>
            <Segmented label="Indicator" options={[...METRICS]} value={metric} onChange={(v) => setParam("metric", v)} />
          </div>
        </CardBody>
      </Card>

      {catalog.isError ? <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} className="mb-4" /> : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="min-w-0 xl:col-span-2">
          <WidgetBoundary label="Comparison chart">
            <ChartFrame
              title={`${METRICS.find((m) => m.value === metric)?.label} · ${selected.join(", ") || "no countries selected"}`}
              description="Aligned on period; the same units are required before series share an axis."
              series={[]}
              isLoading={catalog.isPending}
              emptyTitle={selected.length ? "No observations to compare yet" : "Select at least one country"}
              emptyMessage={
                selected.length
                  ? "Stored series are plotted here from Phase 4. The table shows what each source publishes and how much is stored."
                  : "Use the country chips above."
              }
              allowKindToggle
              exportName={`macropulse-compare-${metric}`}
              height={300}
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
                {selected.length > 1 ? "Same source series and scope for all selected countries." : "Select two or more countries to check comparability."}
              </p>
            )}
          </CardBody>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader title="Per-country source" />
        <CardBody>
          <div className="relative -mx-5 overflow-x-auto px-5">
            <table className="w-full min-w-[640px] text-left text-sm">
              <caption className="sr-only">Source mapping per selected country</caption>
              <thead>
                <tr className="border-b border-line text-xs text-fg-subtle">
                  <th scope="col" className="py-2 pr-4 font-medium">Country</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Source · dataset</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Status</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Latest in probe</th>
                  <th scope="col" className="py-2 font-medium">Note</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ iso2, entry }) => (
                  <tr key={iso2} className="border-b border-line/60 align-top last:border-0">
                    <th scope="row" className="py-3 pr-4 font-mono text-fg">{iso2}</th>
                    <td className="py-3 pr-4 text-fg-muted">{entry ? sourceLabel(entry) ?? "—" : "…"}</td>
                    <td className="py-3 pr-4">
                      {entry ? (
                        <Badge tone={MAPPING_STATUS[entry.mapping.status].tone} dashed={MAPPING_STATUS[entry.mapping.status].tone === "neutral"}>
                          {MAPPING_STATUS[entry.mapping.status].label}
                        </Badge>
                      ) : null}
                    </td>
                    <td className="tabular py-3 pr-4 font-mono text-xs text-fg-muted">{entry?.mapping.probe_last_period ?? "—"}</td>
                    <td className="py-3 text-xs text-fg-muted">{entry ? availabilityReason(entry) : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </>
  );
}
