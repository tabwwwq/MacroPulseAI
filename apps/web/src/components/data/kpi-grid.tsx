"use client";

import type { CatalogEntry } from "@macropulse/shared-types";

import { KpiCard } from "@/components/data/kpi-card";
import { ErrorState } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { formatRelative } from "@/lib/format";
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { useCatalog } from "@/lib/queries";

/** Latest successful fetch across the sources mapped for this country (data freshness). */
function freshness(entries: CatalogEntry[]): string | null {
  const stamps = entries
    .map((e) => e.ingestion.source_last_success_at)
    .filter((s): s is string => Boolean(s))
    .sort();
  return stamps.at(-1) ?? null;
}

/**
 * Headline KPIs for one country: the four KPI indicators from the catalog, the model risk and data
 * freshness. Every tile is wired to the API and shows a reason instead of a number until data exists.
 */
export function KpiGrid({ iso2, asOf }: { iso2: string; asOf: string | null }) {
  const catalog = useCatalog(iso2);

  if (catalog.isError) return <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} />;

  const entries = catalog.data?.countries[0]?.items ?? [];
  const kpis = entries.filter((e) => e.indicator.kpi);
  const fresh = freshness(entries);

  return (
    <section aria-label="Headline indicators" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
      {catalog.isPending
        ? Array.from({ length: 6 }, (_, i) => <KpiCard key={i} label="Loading" isLoading />)
        : kpis.map((e) => {
            const status = MAPPING_STATUS[e.mapping.status];
            return (
              <KpiCard
                key={e.indicator.id}
                label={e.indicator.name}
                unit={e.indicator.unit}
                value={null}
                badge={{ label: status.label, tone: status.tone }}
                note={availabilityReason(e)}
                source={sourceLabel(e)}
              />
            );
          })}
      {!catalog.isPending ? (
        <>
          <KpiCard
            label="Recession risk · next 2Q"
            value={null}
            badge={{ label: "No model", tone: "neutral" }}
            note={`No trained model yet (training arrives in Phase 5). Estimates will state model version and the as-of quarter (${formatAsOf(asOf)}).`}
          />
          <KpiCard
            label="Data freshness"
            value={null}
            badge={fresh ? { label: "Synced", tone: "ok" } : { label: "Never synced", tone: "neutral" }}
            note={
              fresh
                ? `Last successful fetch ${formatRelative(fresh)}.`
                : "No official source has been fetched yet. Freshness = last successful fetch, not the observation period."
            }
          />
        </>
      ) : null}
    </section>
  );
}
