import { describe, expect, it } from "vitest";

import type { IndicatorSeries } from "@macropulse/shared-types";

import type { ChartSeries } from "@/components/charts/types";
import {
  clipShading,
  flagLabel,
  parseRange,
  provenanceLabel,
  rangeBounds,
  referenceShading,
  spreadVsBaseline,
  toChartSeries,
} from "@/lib/series";

const NOW = new Date(Date.UTC(2026, 10, 9));

function series(overrides: Partial<IndicatorSeries> = {}): IndicatorSeries {
  return {
    country: "DE",
    indicator: {
      id: "policy_rate",
      name: "Policy rate",
      category: "monetary",
      unit: "% p.a.",
      frequency: "event",
      description: "",
      kpi: true,
    },
    unit: "% per annum",
    transform: "As published by the source.",
    scope_note: "Shared euro area rate — not a national central-bank rate.",
    note: "",
    points: [
      { period: "2026-06-17", value: 2.25 },
      { period: "2026-09-16", value: 2.5 },
    ],
    truncated: false,
    provenance: {
      source_id: "ecb",
      source_name: "ECB Data Portal API",
      docs_url: null,
      dataset: "FM",
      series_key: "B.U2.EUR.4F.KR.DFR.LEV",
      series_id: "ecb:FM:B.U2.EUR.4F.KR.DFR.LEV:EA",
      native_unit: "% per annum",
      adjustment: null,
      request_url: "https://data-api.ecb.europa.eu/x",
      retrieved_at: "2026-11-09T11:36:11Z",
      source_updated_at: null,
      native_observations: 69,
    },
    quality: [],
    ...overrides,
  };
}

describe("ranges", () => {
  it("falls back to the default for unknown values", () => {
    expect(parseRange("10y")).toBe("10y");
    expect(parseRange("1000y")).toBe("10y");
    expect(parseRange(null)).toBe("10y");
  });

  it("counts whole years back from now or from the as-of quarter, and stops at the cut-off", () => {
    expect(rangeBounds("5y", null, NOW)).toEqual({ start: "2022" });
    expect(rangeBounds("10y", "2008-Q4", NOW)).toEqual({ start: "1999", end: "2008-Q4" });
    expect(rangeBounds("max", "2008-Q4", NOW)).toEqual({ end: "2008-Q4" });
    expect(rangeBounds("max", null, NOW)).toEqual({});
  });
});

describe("toChartSeries", () => {
  it("keeps values, names the source and draws event-dated series as steps", () => {
    const s = toChartSeries(series(), "DE");
    expect(s).toMatchObject({ id: "DE-policy_rate", name: "DE", unit: "% per annum", source: "ECB · FM", step: true });
    expect(s.points).toEqual([
      { period: "2026-06-17", value: 2.25 },
      { period: "2026-09-16", value: 2.5 },
    ]);
    expect(s.citation).toBe(
      "ECB Data Portal API, FM B.U2.EUR.4F.KR.DFR.LEV; As published by the source. Retrieved 2026-11-09",
    );
  });

  it("labels the publisher compactly", () => {
    expect(provenanceLabel(series().provenance)).toBe("ECB · FM");
    expect(provenanceLabel({ ...series().provenance, source_id: "eurostat", source_name: "Eurostat dissemination API", dataset: "namq_10_gdp" })).toBe(
      "Eurostat · namq_10_gdp",
    );
  });
});

describe("referenceShading", () => {
  it("turns runs of 1 into labelled ranges and keeps runs that touch the end", () => {
    const points = [
      { period: "2007-11", value: 0 },
      { period: "2007-12", value: 1 },
      { period: "2008-01", value: 1 },
      { period: "2009-06", value: 1 },
      { period: "2009-07", value: 0 },
      { period: "2020-03", value: 1 },
      { period: "2020-04", value: 1 },
    ];
    const shading = referenceShading(points);
    expect(shading.map(({ from, to }) => [from, to])).toEqual([
      ["2007-12", "2009-06"],
      ["2020-03", "2020-04"],
    ]);
    expect(shading[0]?.label).toContain("NBER");
  });

  it("drops ranges that end before the first visible period", () => {
    const shading = [
      { from: "2001-04", to: "2001-11", label: "x" },
      { from: "2020-03", to: "2020-04", label: "x" },
    ];
    expect(clipShading(shading, "2016-Q1").map((s) => s.from)).toEqual(["2020-03"]);
    expect(clipShading(shading, undefined)).toEqual([]);
  });
});

describe("spreadVsBaseline", () => {
  const de: ChartSeries = { id: "de", name: "DE", unit: "%", points: [{ period: "2026-08", value: 2 }, { period: "2026-09", value: 2.5 }] };
  const fr: ChartSeries = {
    id: "fr",
    name: "FR",
    unit: "%",
    points: [
      { period: "2026-07", value: 1 },
      { period: "2026-08", value: 3 },
      { period: "2026-09", value: null },
    ],
  };

  it("differences only periods both series published, in percentage points", () => {
    const [spread] = spreadVsBaseline([de, fr]);
    expect(spread).toMatchObject({ name: "FR − DE", unit: "pp" });
    expect(spread?.points).toEqual([{ period: "2026-08", value: 1 }]);
  });

  it("returns nothing for a lone baseline", () => {
    expect(spreadVsBaseline([de])).toEqual([]);
    expect(spreadVsBaseline([])).toEqual([]);
  });
});

describe("flagLabel", () => {
  it("translates source flags and hides the SDMX normal status", () => {
    expect(flagLabel("p")).toBe("provisional");
    expect(flagLabel("e")).toBe("estimated");
    expect(flagLabel("b")).toBe("break in series");
    expect(flagLabel("A")).toBeNull();
    expect(flagLabel(null)).toBeNull();
    expect(flagLabel("z")).toBe("source flag “z”");
  });
});
