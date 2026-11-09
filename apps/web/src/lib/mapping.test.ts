import { describe, expect, it } from "vitest";

import type { CatalogEntry, MappingStatus } from "@macropulse/shared-types";

import { availabilityReason, sourceLabel } from "@/lib/mapping";

function entry(status: MappingStatus, overrides: Partial<CatalogEntry["mapping"]> = {}, observations = 0): CatalogEntry {
  return {
    indicator: {
      id: "x",
      name: "X",
      category: "growth",
      unit: "%",
      frequency: "quarterly",
      description: "",
      kpi: true,
    },
    mapping: {
      status,
      source_id: "eurostat",
      source_name: "Eurostat dissemination API",
      docs_url: "https://example.org",
      dataset: "namq_10_gdp",
      series_key: "k",
      native_frequency: "quarterly",
      adjustment: null,
      probe_last_period: "2026-Q3",
      probe_date: "2026-11-08",
      note: "",
      scope_note: "",
      ...overrides,
    },
    ingestion: { observations, latest_period: null, source_last_success_at: null },
  };
}

describe("availabilityReason", () => {
  it("states that verified series are not ingested yet (never implies a value)", () => {
    expect(availabilityReason(entry("verified"))).toBe("Series verified on 2026-11-08 (latest 2026-Q3); not ingested yet.");
  });

  it("reports stored observations once they exist", () => {
    expect(availabilityReason(entry("verified", {}, 120))).toBe("120 observations stored.");
  });

  it("uses the finding note for stale and unpublished series", () => {
    expect(availabilityReason(entry("stale", { note: "Ends 2025-12 (F-001)." }))).toBe("Ends 2025-12 (F-001).");
    expect(availabilityReason(entry("not_published", { note: "OECD publishes no CLI." }))).toBe("OECD publishes no CLI.");
    expect(availabilityReason(entry("unmapped", { note: "" }))).toBe("No official source mapped for this country yet.");
  });
});

describe("sourceLabel", () => {
  it("names publisher and dataset, or nothing when unmapped", () => {
    expect(sourceLabel(entry("verified"))).toBe("Eurostat · namq_10_gdp");
    expect(sourceLabel(entry("verified", { source_id: "fred", source_name: "FRED / ALFRED API", dataset: "GDPC1" }))).toBe("FRED · GDPC1");
    expect(sourceLabel(entry("unmapped", { source_name: null, dataset: null }))).toBeNull();
  });
});
