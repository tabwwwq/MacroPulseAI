"use client";

import type { ReactNode } from "react";

import { ChartFrame } from "@/components/charts/chart-frame";
import type { ChartKind } from "@/components/charts/types";
import { Badge } from "@/components/ui/badge";
import { ApiError } from "@/lib/api";
import { useIndicatorSeries } from "@/lib/queries";
import { clipShading, provenanceLabel, rangeBounds, referenceShading, toChartSeries, type RangeKey } from "@/lib/series";

export interface IndicatorChartProps {
  iso2: string;
  indicator: string;
  title?: string;
  /** Extra description (badges, scope) rendered after the unit line. */
  extra?: ReactNode;
  asOf: string | null;
  range: RangeKey;
  height?: number;
  /** Shade the NBER reference chronology (US only; never the model target). */
  reference?: boolean;
  allowKindToggle?: boolean;
  defaultKind?: ChartKind;
}

/** Expected answers ("not published", "not synced") are empty states, not errors. */
export function isExpectedAbsence(error: unknown): error is ApiError {
  return error instanceof ApiError && (error.status === 404 || error.status === 503);
}

/**
 * One stored official series drawn with its provenance: unit, frequency, derivation, source link to
 * the exact request, retrieval time and the latest quality warnings. Nothing is interpolated.
 */
export function IndicatorChart({
  iso2,
  indicator,
  title,
  extra,
  asOf,
  range,
  height = 240,
  reference = false,
  allowKindToggle = true,
  defaultKind = "line",
}: IndicatorChartProps) {
  const bounds = rangeBounds(range, asOf);
  const query = useIndicatorSeries({ country: iso2, indicator, ...bounds });
  const nber = useIndicatorSeries(reference && iso2 === "US" ? { country: "US", indicator: "nber_recession", ...bounds } : null);
  const data = query.data;
  const absent = isExpectedAbsence(query.error) ? query.error : null;
  const series = data ? [toChartSeries(data)] : [];
  const shading = nber.data ? clipShading(referenceShading(nber.data.points), data?.points[0]?.period) : [];
  const issues = data?.quality.filter((c) => c.status !== "pass") ?? [];
  const flags = data?.quality.find((c) => c.rule === "source_flags");

  const description = (
    <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
      {data ? (
        <span>
          {data.unit} · {data.indicator.frequency} · {data.transform}
          {data.provenance.adjustment ? ` Source series: ${data.provenance.adjustment}.` : ""}
        </span>
      ) : null}
      {data?.scope_note ? <span className="text-warn">{data.scope_note}</span> : null}
      {asOf ? <Badge tone="neutral">to {asOf}</Badge> : null}
      {extra}
    </span>
  );

  const notes =
    issues.length || flags || shading.length ? (
      <ul className="mt-3 space-y-1 text-xs">
        {issues.map((c) => (
          <li key={c.rule} className={c.status === "fail" ? "text-danger" : "text-warn"}>
            {c.status === "fail" ? "Failed" : "Warning"} · {c.rule.replaceAll("_", " ")}: {c.detail}
          </li>
        ))}
        {flags ? <li className="text-fg-subtle">{flags.detail}</li> : null}
        {shading.length ? (
          <li className="text-fg-subtle">
            Amber bands: NBER recession dates (FRED USREC) — an external reference, not the GDP-based technical-recession
            target.
          </li>
        ) : null}
      </ul>
    ) : null;

  return (
    <ChartFrame
      title={title ?? data?.indicator.name ?? indicator}
      description={description}
      series={series}
      isLoading={query.isPending}
      error={absent ? undefined : query.error}
      onRetry={() => void query.refetch()}
      emptyTitle={absent ? (absent.status === 503 ? "Not synced yet" : "Not available for this country") : "No observations in this window"}
      emptyMessage={
        absent
          ? absent.message
          : "No stored observation falls inside the selected range and as-of cut-off. Missing data is not estimated."
      }
      source={
        data
          ? {
              label: `${provenanceLabel(data.provenance)} · ${data.provenance.native_observations} stored observations`,
              href: data.provenance.request_url,
              retrievedAt: data.provenance.retrieved_at,
            }
          : undefined
      }
      shading={shading}
      notes={notes}
      allowKindToggle={allowKindToggle}
      defaultKind={defaultKind}
      exportName={`macropulse-${iso2.toLowerCase()}-${indicator}${asOf ? `-asof-${asOf}` : ""}`}
      height={height}
    />
  );
}
