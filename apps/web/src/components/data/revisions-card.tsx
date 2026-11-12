"use client";

import { History } from "lucide-react";

import type { Revisions } from "@macropulse/shared-types";

import { ChartFrame } from "@/components/charts/chart-frame";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { useRevisions } from "@/lib/queries";
import { formatSigned, largestRevisions, revisionChartSeries, signalLabel } from "@/lib/revisions";
import { rangeBounds, type RangeKey } from "@/lib/series";

/** Indicators with a stored ALFRED revision history (US only). */
export const REVISION_INDICATORS = ["real_gdp_qoq", "inflation_yoy", "unemployment_rate"] as const;

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-line bg-canvas/50 px-3 py-2.5">
      <p className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-fg-subtle">{label}</p>
      <p className="tabular mt-1 font-mono text-lg font-semibold text-fg">{value}</p>
      {hint ? <p className="mt-0.5 text-[11px] text-fg-subtle">{hint}</p> : null}
    </div>
  );
}

/** Revisions of one US series as data: statistics, recession signals, largest revisions. */
export function RevisionsDetails({ data }: { data: Revisions }) {
  const unit = data.revision_unit;
  const genuine = data.points.filter((p) => p.first_release);
  const excluded = data.points.length - genuine.length;
  const largest = largestRevisions(data);
  const s = data.summary;

  return (
    <div className="mt-4 space-y-4">
      <div className="grid gap-2 sm:grid-cols-3">
        <Stat
          label="Mean |revision| · all"
          value={s.mean_abs_revision === null ? "N/A" : `${s.mean_abs_revision.toFixed(2)} ${unit}`}
          hint={`${s.count} first releases`}
        />
        <Stat
          label="Largest"
          value={s.max_abs_revision === null ? "N/A" : `${s.max_abs_revision.toFixed(2)} ${unit}`}
          hint={s.max_abs_period ?? undefined}
        />
        <Stat
          label="Sign flipped"
          value={String(s.sign_changes.length)}
          hint={s.sign_changes.length ? `latest: ${s.sign_changes.at(-1)}` : "never"}
        />
      </div>

      {data.technical_signals.length ? (
        <section aria-label="Technical-recession signals, first release versus today">
          <h3 className="mb-2 text-sm font-medium text-fg">Two negative quarters in a row — then and now</h3>
          <ul className="divide-y divide-line/60 rounded-xl border border-line">
            {data.technical_signals.map((t) => {
              const tag = signalLabel(t);
              return (
                <li key={t.period} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-3 py-2 text-xs">
                  <span className="w-16 font-mono text-fg">{t.period}</span>
                  <span className="tabular min-w-0 flex-1 font-mono text-fg-muted">
                    first known {t.published}: {t.first_values.map((v) => formatSigned(v)).join(" / ")} · today:{" "}
                    {t.latest_values.map((v) => formatSigned(v)).join(" / ")}
                  </span>
                  <Badge tone={tag.tone}>{tag.label}</Badge>
                </li>
              );
            })}
          </ul>
          <p className="mt-2 text-[11px] leading-relaxed text-fg-subtle">
            Quarter shown = the second of two consecutive negative q/q readings. &ldquo;First known&rdquo; takes
            both quarters from the vintage of the day the second one was first published.
          </p>
        </section>
      ) : null}

      {largest.length ? (
        <div
          className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent"
          tabIndex={0}
          role="region"
          aria-label="Table, scrolls horizontally"
        >
          <table className="w-full min-w-[480px] text-left text-sm">
            <caption className="mb-2 text-left text-sm font-medium text-fg">Largest revisions</caption>
            <thead className="text-fg-subtle">
              <tr>
                <th scope="col" className="py-2 pr-4 font-medium">Period</th>
                <th scope="col" className="py-2 pr-4 font-medium">First published</th>
                <th scope="col" className="py-2 pr-4 text-right font-medium">First release</th>
                <th scope="col" className="py-2 pr-4 text-right font-medium">Today</th>
                <th scope="col" className="py-2 text-right font-medium">Revision ({unit})</th>
              </tr>
            </thead>
            <tbody className="tabular font-mono text-xs">
              {largest.map((p) => (
                <tr key={p.period} className="border-t border-line/60">
                  <th scope="row" className="py-2 pr-4 font-normal text-fg">{p.period}</th>
                  <td className="py-2 pr-4 text-fg-muted">{p.first_published}</td>
                  <td className="py-2 pr-4 text-right text-fg">{formatSigned(p.first_value)}</td>
                  <td className="py-2 pr-4 text-right text-fg">{formatSigned(p.latest_value)}</td>
                  <td className="py-2 text-right text-fg">{formatSigned(p.revision)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <p className="text-[11px] leading-relaxed text-fg-subtle">
        {data.note}
        {excluded ? ` ${excluded} earlier or back-filled periods are not first releases and are left out.` : ""}
      </p>
    </div>
  );
}

/**
 * How much one US indicator changed between its first publication and today (ALFRED vintages).
 * Renders nothing outside the US: Eurostat and the ECB serve the latest revision only.
 */
export function RevisionsCard({ iso2, indicator, range }: { iso2: string; indicator: string; range: RangeKey }) {
  const us = iso2.toUpperCase() === "US";
  const query = useRevisions(iso2, indicator, us);
  if (!us) return null;

  if (query.isPending) {
    return (
      <Card aria-label="Revision history">
        <CardBody>
          <Skeleton className="h-64 w-full" />
        </CardBody>
      </Card>
    );
  }
  if (query.isError) {
    const err = query.error;
    if (err instanceof ApiError && err.code === "vintages_not_synced") {
      return (
        <Card aria-label="Revision history">
          <CardHeader title="Revision history" description="First release versus today (ALFRED)." />
          <CardBody>
            <EmptyState icon={<History className="size-5" aria-hidden />} title="Revision history not synced">
              {err.message}
            </EmptyState>
          </CardBody>
        </Card>
      );
    }
    return <ErrorState error={err} onRetry={() => void query.refetch()} />;
  }

  const data = query.data;
  // The chart follows the page's range control (over 35 years the two lines merge); statistics,
  // signals and the table always cover every first release.
  const start = rangeBounds(range, null).start;
  const series = revisionChartSeries(data).map((s) => ({
    ...s,
    points: start ? s.points.filter((p) => p.period >= start) : s.points,
  }));
  return (
    <ChartFrame
      title={`${data.indicator.name}: first release vs today`}
      description={
        <span className="flex flex-wrap items-center gap-2">
          <span>
            {data.indicator.unit} · {data.transform} Each value as first published, next to the same period in
            today&apos;s data. The chart follows the range above; the figures below cover all first releases.
          </span>
          <Badge tone="accent">Vintage data</Badge>
        </span>
      }
      series={series}
      source={{
        label: `ALFRED · ${data.series.dataset} · ${data.series.vintages} vintages`,
        href: data.series.source_url,
        retrievedAt: data.series.retrieved_at,
      }}
      notes={<RevisionsDetails data={data} />}
      height={260}
      exportName={`macropulse-us-${data.indicator.id}-revisions`}
    />
  );
}
