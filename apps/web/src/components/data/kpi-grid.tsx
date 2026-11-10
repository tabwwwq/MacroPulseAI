"use client";

import type { CatalogEntry, KpiValue } from "@macropulse/shared-types";

import { KpiCard } from "@/components/data/kpi-card";
import { ProvenanceDetails } from "@/components/data/provenance";
import { ErrorState } from "@/components/ui/states";
import { formatRelative } from "@/lib/format";
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { modelState, modelSummaryText } from "@/lib/models";
import { useCatalog, useCountrySummary, useModels, useRecessionEstimate } from "@/lib/queries";
import { BANDS, formatProbability } from "@/lib/risk";
import { ApiError } from "@/lib/api";
import { flagLabel, provenanceLabel } from "@/lib/series";

/** Change unit: percentage points for rates, otherwise the indicator unit. */
export function changeUnit(unit: string): string {
  return unit.startsWith("%") ? "pp" : unit;
}

function KpiTile({ kpi, entry }: { kpi: KpiValue; entry: CatalogEntry | undefined }) {
  const status = entry ? MAPPING_STATUS[entry.mapping.status] : null;
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
            <KpiTile key={k.indicator.id} kpi={k} entry={entries.find((e) => e.indicator.id === k.indicator.id)} />
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
