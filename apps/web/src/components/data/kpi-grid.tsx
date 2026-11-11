"use client";

import type { CatalogEntry, KpiValue } from "@macropulse/shared-types";

import { KpiCard } from "@/components/data/kpi-card";
import { ProvenanceDetails } from "@/components/data/provenance";
import { ErrorState } from "@/components/ui/states";
import { formatRelative } from "@/lib/format";
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { modelState, modelSummaryText } from "@/lib/models";
import { useCatalog, useCountrySummary, useIndicatorSeries, useModels, useRecessionEstimate } from "@/lib/queries";
import { BANDS, formatProbability } from "@/lib/risk";
import { ApiError } from "@/lib/api";
import { flagLabel, provenanceLabel, rangeBounds } from "@/lib/series";

/** Change unit: percentage points for rates, otherwise the indicator unit. */
export function changeUnit(unit: string): string {
  return unit.startsWith("%") ? "pp" : unit;
}

/** How many of the latest stored observations the KPI sparkline shows. */
export const TREND_POINTS = 24;

/**
 * Sparkline input: the last stored observations of the same series the KPI value comes from, up to
 * and including the KPI's own period. `null` when there is nothing to draw.
 */
export function kpiTrend(
  points: { period: string; value: number | null }[] | undefined,
  kpi: Pick<KpiValue, "period" | "indicator">,
): { values: (number | null)[]; label: string } | null {
  if (!points?.length || !kpi.period) return null;
  const end = points.findIndex((p) => p.period === kpi.period);
  if (end < 0) return null;
  const window = points.slice(Math.max(0, end + 1 - TREND_POINTS), end + 1);
  const first = window[0];
  if (!first || window.length < 2) return null;
  return {
    values: window.map((p) => p.value),
    label: `${kpi.indicator.name}: ${window.length} stored observations from ${first.period} to ${kpi.period}`,
  };
}

function KpiTile({ kpi, entry, iso2, asOf }: { kpi: KpiValue; entry: CatalogEntry | undefined; iso2: string; asOf: string | null }) {
  const status = entry ? MAPPING_STATUS[entry.mapping.status] : null;
  // Same query as the overview charts (10-year window), so this is served from the cache there.
  const series = useIndicatorSeries(
    kpi.status === "ok" ? { country: iso2, indicator: kpi.indicator.id, ...rangeBounds("10y", asOf) } : null,
  );
  const trend = kpiTrend(series.data?.points, kpi);
  const flag = flagLabel(kpi.source_flag);
  const note =
    kpi.status === "ok"
      ? kpi.scope_note || (kpi.stale ? `Latest period ended ${kpi.days_since_period_end} days before the cut-off.` : null)
      : (kpi.reason ?? (entry ? availabilityReason(entry) : null));
  return (
    <KpiCard
      label={kpi.indicator.name}
      unit={kpi.unit}
      value={kpi.value}
      period={kpi.period}
      stale={kpi.stale}
      change={kpi.change}
      changeUnit={changeUnit(kpi.unit)}
      previousPeriod={kpi.previous_period}
      flag={flag}
      badge={status ? { label: status.label, tone: status.tone } : undefined}
      note={note}
      trend={trend ?? undefined}
      source={kpi.provenance ? provenanceLabel(kpi.provenance) : entry ? sourceLabel(entry) : null}
      provenance={
        kpi.provenance ? (
          <ProvenanceDetails provenance={kpi.provenance} transform={kpi.transform} period={kpi.period} flag={flag} />
        ) : undefined
      }
    />
  );
}

/**
 * Headline KPIs for one country: latest stored value, change, staleness and provenance for each KPI
 * indicator, then the model state (read from /api/models) and data freshness. No tile shows a number that
 * is not a stored official observation (or its documented derivation).
 */
export function KpiGrid({ iso2, asOf }: { iso2: string; asOf: string | null }) {
  const summary = useCountrySummary(iso2, asOf);
  const catalog = useCatalog(iso2);
  const models = modelState(useModels().data);
  const risk = useRecessionEstimate(iso2, 2, asOf);

  if (summary.isError) return <ErrorState error={summary.error} onRetry={() => void summary.refetch()} />;

  const entries = catalog.data?.countries[0]?.items ?? [];
  const fresh = summary.data?.freshness ?? null;

  return (
    <section aria-label="Headline indicators" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
      {summary.isPending
        ? Array.from({ length: 6 }, (_, i) => <KpiCard key={i} label="Loading" isLoading />)
        : summary.data.kpis.map((k) => (
            <KpiTile
              key={k.indicator.id}
              kpi={k}
              entry={entries.find((e) => e.indicator.id === k.indicator.id)}
              iso2={iso2}
              asOf={asOf}
            />
          ))}
      {summary.data ? (
        <>
          {risk.data ? (
            <KpiCard
              label="Recession risk · next 2Q"
              unit="%"
              value={Math.round(risk.data.probability * 1000) / 10}
              period={`as of ${risk.data.as_of}`}
              badge={{
                label: BANDS[risk.data.band]?.label ?? risk.data.band,
                tone: BANDS[risk.data.band]?.tone ?? "neutral",
              }}
              note={[
                `Technical-recession probability · base rate ${formatProbability(risk.data.base_rate)}.`,
                risk.data.track_record.beats_baseline_heldout === false
                  ? "Does not beat the base rate on 2015+ held-out years."
                  : "",
                risk.data.in_sample ? "In-sample fit for this as-of quarter." : "",
              ]
                .filter(Boolean)
                .join(" ")}
              source={`Model · ${risk.data.model.id}`}
            />
          ) : (
            <KpiCard
              label="Recession risk · next 2Q"
              value={null}
              isLoading={risk.isPending && models.trained}
              badge={models.trained ? { label: "No estimate", tone: "warn" } : { label: "No model", tone: "neutral" }}
              note={risk.error instanceof ApiError ? risk.error.message : modelSummaryText(models)}
            />
          )}
          <KpiCard
            label="Data freshness"
            value={null}
            badge={fresh ? { label: "Synced", tone: "ok" } : { label: "Never synced", tone: "neutral" }}
            note={
              fresh
                ? `Last successful fetch ${formatRelative(fresh)}. Freshness is the fetch time, not the observation period.${asOf ? ` Values shown for periods ending by ${summary.data.cutoff}.` : ""}`
                : "No official source has been fetched yet. Freshness = last successful fetch, not the observation period."
            }
          />
        </>
      ) : null}
    </section>
  );
}
