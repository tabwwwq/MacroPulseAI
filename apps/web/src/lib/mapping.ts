import type { CatalogEntry, MappingStatus } from "@macropulse/shared-types";

type Tone = "ok" | "accent" | "warn" | "neutral";

export const MAPPING_STATUS: Record<MappingStatus, { label: string; tone: Tone }> = {
  verified: { label: "Source verified", tone: "ok" },
  partial: { label: "Values verified", tone: "accent" },
  stale: { label: "Source stale", tone: "warn" },
  not_published: { label: "Not published", tone: "neutral" },
  unmapped: { label: "Not mapped", tone: "neutral" },
};

/** "Eurostat · namq_10_gdp" */
export function sourceLabel(entry: CatalogEntry): string | null {
  const m = entry.mapping;
  if (!m.source_name || !m.dataset) return null;
  const publisher = m.source_id === "fred" ? "FRED" : m.source_name.split(" ")[0];
  return `${publisher} · ${m.dataset}`;
}

/**
 * Why there is no value to show yet, in one honest sentence derived from the probe metadata.
 * (Observations are ingested from Phase 3; until then every KPI is unavailable.)
 */
export function availabilityReason(entry: CatalogEntry): string {
  const m = entry.mapping;
  const stored = entry.ingestion.observations;
  switch (m.status) {
    case "verified":
      return stored > 0
        ? `${stored} observations stored.`
        : `Series verified on ${m.probe_date} (latest ${m.probe_last_period}); not ingested yet.`;
    case "partial":
      return `Values verified on ${m.probe_date}; ${m.note || "metadata pending"} Not ingested yet.`;
    case "stale":
      return m.note || `Source series ends ${m.probe_last_period}.`;
    case "not_published":
      return m.note || "Not published by the source for this country.";
    case "unmapped":
      return m.note || "No official source mapped for this country yet.";
  }
}
