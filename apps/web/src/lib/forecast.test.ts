import { describe, expect, it } from "vitest";

import type { ForecastResponse } from "@macropulse/shared-types";

import {
  backtestSeries,
  coverageStatus,
  forecastToCsv,
  horizonLabel,
  metricGroups,
  parseHorizon,
  parseMetric,
  pickModel,
} from "@/lib/forecast";

const metric = (model: string, horizon: number, rmse: number | null, coverage: number | null) => ({
  model,
  step: horizon,
  horizon_quarters: horizon,
  n: rmse === null ? 5 : 80,
  mae: rmse,
  rmse,
  bias: 0,
  rel_rmse: rmse,
  coverage,
  coverage_n: coverage === null ? 0 : 60,
  mean_width: 1,
  note: rmse === null ? "Only 5 scored forecasts (needs 20)." : null,
});

const fc: ForecastResponse = {
  country: "DE",
  metric: "real_gdp_qoq",
  indicator_name: "Real GDP growth",
  unit: "% q/q",
  frequency: "quarterly",
  horizon_quarters: 2,
  steps: 2,
  as_of: "2010-Q2",
  cutoff: "2010-06-30",
  origin: "2010-Q1",
  version: "forecast-v1",
  nominal_coverage: 0.8,
  min_errors: 20,
  actuals: [
    { period: "2009-Q4", value: 0.7 },
    { period: "2010-Q1", value: 0.6 },
  ],
  realised: [{ period: "2010-Q2", value: 2.1 }],
  models: [
    { key: "naive", name: "Naive (last value)", description: "", available: true, reason: null, path: [] },
    {
      key: "ar",
      name: "Direct ridge AR",
      description: "",
      available: true,
      reason: null,
      path: [
        { period: "2010-Q2", step: 1, value: 0.5, lower: -0.4, upper: 1.3, n_errors: 70 },
        { period: "2010-Q3", step: 2, value: 0.45, lower: null, upper: null, n_errors: 12 },
      ],
    },
  ],
  backtest: {
    first_origin: "1995-Q1",
    last_origin: "2009-Q4",
    metrics: [metric("naive", 1, 0.9, 0.8), metric("ar", 1, 0.7, 0.62), metric("ar", 2, null, null)],
  },
  errors: [
    { model: "ar", origin: "2009-Q2", target: "2009-Q4", forecast: 0.2, actual: 0.7, error: 0.5 },
    { model: "naive", origin: "2009-Q2", target: "2009-Q4", forecast: 0.3, actual: 0.7, error: 0.4 },
  ],
  assumptions: [],
  transform: "q/q",
  provenance: {
    source_id: "eurostat",
    source_name: "Eurostat",
    docs_url: null,
    dataset: "namq_10_gdp",
    series_key: "Q.CLV20_MNAC.SCA.B1GQ",
    series_id: "x",
    native_unit: "CLV20_MNAC",
    adjustment: "SCA",
    request_url: "https://example.invalid",
    retrieved_at: "2026-11-09T12:00:00Z",
    source_updated_at: null,
    native_observations: 120,
  },
  generated_at: "2026-11-10T12:00:00Z",
};

describe("URL parameters", () => {
  it("falls back to safe defaults", () => {
    expect(parseMetric("unemployment_rate")).toBe("unemployment_rate");
    expect(parseMetric("oil")).toBe("real_gdp_qoq");
    expect(parseHorizon("8")).toBe("8");
    expect(parseHorizon("3")).toBe("4");
    expect(horizonLabel(4, "monthly")).toBe("4 quarters · 12 months");
    expect(horizonLabel(1, "quarterly")).toBe("1 quarter");
  });

  it("defaults to the pre-specified AR challenger, not the best backtest score", () => {
    expect(pickModel(fc.models, null)?.key).toBe("ar");
    expect(pickModel(fc.models, "naive")?.key).toBe("naive");
    expect(pickModel(fc.models, "unknown")?.key).toBe("ar");
  });
});

describe("diagnostics", () => {
  it("flags under-coverage and keeps missing coverage as N/A", () => {
    expect(coverageStatus(0.62, 0.8)).toBe("under");
    expect(coverageStatus(0.75, 0.8)).toBe("ok");
    expect(coverageStatus(null, 0.8)).toBe("na");
  });

  it("groups by horizon and marks the lowest RMSE only among scored rows", () => {
    const groups = metricGroups(fc.backtest.metrics);
    expect(groups.map((g) => g.horizon)).toEqual([1, 2]);
    expect(groups[0]?.best).toBe("ar");
    expect(groups[1]?.best).toBeNull();
  });

  it("places backtest forecasts at their target period next to the published value", () => {
    const ar = pickModel(fc.models, "ar");
    if (!ar) throw new Error("model missing");
    const [published, forecast] = backtestSeries(fc, ar);
    expect(published?.points).toEqual([{ period: "2009-Q4", value: 0.7 }]);
    expect(forecast?.points).toEqual([{ period: "2009-Q4", value: 0.2 }]);
    expect(forecast?.name).toBe("Direct ridge AR, forecast 2 quarters earlier");
    expect(published?.citation).toContain("retrieved 2026-11-09");
  });
});

describe("forecastToCsv", () => {
  it("writes published, forecast and later-published rows with unit, origin and source", () => {
    const ar = pickModel(fc.models, "ar");
    if (!ar) throw new Error("model missing");
    const lines = forecastToCsv(fc, ar).trimEnd().split("\r\n");
    expect(lines[0]).toBe("period,type,model,step,value,lower_80,upper_80,unit,forecast_origin,version,source");
    expect(lines).toHaveLength(1 + 2 + 2 + 1);
    expect(lines[3]).toMatch(/^2010-Q2,forecast,ar,1,0.5,-0.4,1.3,% q\/q,2010-Q1,forecast-v1,/);
    expect(lines[4]).toMatch(/^2010-Q3,forecast,ar,2,0.45,,,/);
    expect(lines[5]).toMatch(/^2010-Q2,published_after_origin,,,2.1,/);
    expect(lines[1]).toContain("Eurostat namq_10_gdp (Q.CLV20_MNAC.SCA.B1GQ); retrieved 2026-11-09T12:00:00Z");
  });
});
