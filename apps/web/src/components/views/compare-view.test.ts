import { describe, expect, it } from "vitest";

import type { CatalogEntry } from "@macropulse/shared-types";

import { comparabilityWarnings, parseSelection } from "@/components/views/compare-view";

function entry(overrides: Partial<CatalogEntry["mapping"]>): CatalogEntry {
  return {
    indicator: { id: "policy_rate", name: "Policy rate", category: "monetary", unit: "% p.a.", frequency: "event", description: "", kpi: true },
    mapping: {
      status: "verified",
      source_id: "ecb",
      source_name: "ECB Data Portal API",
      docs_url: null,
      dataset: "FM",
      series_key: "B.U2.EUR.4F.KR.DFR.LEV",
      native_frequency: "event",
      adjustment: null,
      probe_last_period: "2026-09-16",
      probe_date: "2026-11-08",
      note: "",
      scope_note: "Shared euro area rate — not a national central-bank rate.",
      ...overrides,
    },
    ingestion: { observations: 69, latest_period: "2026-09-16", source_last_success_at: null },
  };
}

describe("parseSelection", () => {
  it("normalises, de-duplicates and caps at four countries", () => {
    expect(parseSelection("de, fr,DE,nl,us,be", null)).toEqual(["DE", "FR", "NL", "US"]);
  });

  it("drops malformed codes and falls back to the context country", () => {
    expect(parseSelection("xyz,1", "BE")).toEqual(["BE"]);
    expect(parseSelection(null, null)).toEqual([]);
  });
});

describe("comparabilityWarnings", () => {
  it("flags the shared ECB rate and mixed sources and frequencies", () => {
    const fed = entry({ source_id: "fred", dataset: "FEDFUNDS", native_frequency: "monthly", scope_note: "" });
    const warnings = comparabilityWarnings([
      { iso2: "DE", entry: entry({}) },
      { iso2: "FR", entry: entry({}) },
      { iso2: "US", entry: fed },
    ]);
    expect(warnings.some((w) => w.includes("Different source series (FM, FEDFUNDS)"))).toBe(true);
    expect(warnings.some((w) => w.includes("Different native frequencies (event, monthly)"))).toBe(true);
    expect(warnings.some((w) => w.includes("DE, FR share one ECB rate"))).toBe(true);
  });

  it("is silent when every country uses the same series definition", () => {
    const gdp = { dataset: "namq_10_gdp", native_frequency: "quarterly" as const, scope_note: "" };
    expect(
      comparabilityWarnings([
        { iso2: "DE", entry: entry(gdp) },
        { iso2: "NL", entry: entry(gdp) },
      ]),
    ).toEqual([]);
  });
});
