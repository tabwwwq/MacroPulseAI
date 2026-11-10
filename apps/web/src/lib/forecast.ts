import type { ForecastMetric, ForecastModel, ForecastResponse } from "@macropulse/shared-types";

import type { ChartSeries } from "@/components/charts/types";

export const FORECAST_METRICS = [
  { value: "real_gdp_qoq", label: "GDP growth" },
  { value: "inflation_yoy", label: "Inflation" },
  { value: "unemployment_rate", label: "Unemployment" },
] as const;
export type ForecastMetricId = (typeof FORECAST_METRICS)[number]["value"];

export const FORECAST_HORIZONS = ["1", "2", "4", "8"] as const;
export type ForecastHorizon = (typeof FORECAST_HORIZONS)[number];

/** The pre-specified challenger; baselines stay one click away. Not chosen by backtest score. */
export const DEFAULT_MODEL = "ar";

/** Coverage this far below nominal is flagged as under-coverage (binomial noise aside). */
export const UNDER_COVERAGE_MARGIN = 0.1;

export function parseMetric(value: string | null): ForecastMetricId {
  return FORECAST_METRICS.some((m) => m.value === value) ? (value as ForecastMetricId) : "real_gdp_qoq";
}

export function parseHorizon(value: string | null): ForecastHorizon {
  return (FORECAST_HORIZONS as readonly string[]).includes(value ?? "") ? (value as ForecastHorizon) : "4";
}

export function horizonLabel(quarters: number, frequency?: string): string {
  const q = quarters === 1 ? "1 quarter" : `${quarters} quarters`;
  return frequency === "monthly" ? `${q} · ${quarters * 3} months` : q;
}

export function stepUnit(frequency: string, steps: number): string {
  const unit = frequency === "monthly" ? "month" : "quarter";
  return `${steps} ${unit}${steps === 1 ? "" : "s"}`;
}

export function pickModel(models: ForecastModel[], key: string | null): ForecastModel | undefined {
  return models.find((m) => m.key === key) ?? models.find((m) => m.key === DEFAULT_MODEL) ?? models[0];
}

export type CoverageStatus = "ok" | "under" | "na";

export function coverageStatus(coverage: number | null | undefined, nominal: number): CoverageStatus {
  if (typeof coverage !== "number" || !Number.isFinite(coverage)) return "na";
  return coverage < nominal - UNDER_COVERAGE_MARGIN ? "under" : "ok";
}

/** Backtest rows grouped by horizon (quarters), with the lowest-RMSE model of each marked. */
export function metricGroups(metrics: ForecastMetric[]) {
  const byHorizon = new Map<number, ForecastMetric[]>();
  for (const m of metrics) byHorizon.set(m.horizon_quarters, [...(byHorizon.get(m.horizon_quarters) ?? []), m]);
  return [...byHorizon.entries()]
    .sort(([a], [b]) => a - b)
    .map(([horizon, rows]) => {
      const scored = rows.filter((r) => typeof r.rmse === "number");
      const best = scored.length ? scored.reduce((a, b) => ((b.rmse ?? Infinity) < (a.rmse ?? Infinity) ? b : a)).model : null;
      return { horizon, rows, best };
    });
}

/**
 * Backtest chart: what the selected model forecast `steps` periods ahead against what was later
 * published, both placed at the target period.
 */
export function backtestSeries(fc: ForecastResponse, model: ForecastModel): ChartSeries[] {
  const errors = fc.errors.filter((e) => e.model === model.key);
  const citation = `${fc.provenance.source_name} · ${fc.provenance.dataset}; retrieved ${fc.provenance.retrieved_at?.slice(0, 10) ?? "unknown"}`;
  return [
    {
      id: "realised",
      name: "Published value",
      unit: fc.unit,
      points: errors.map((e) => ({ period: e.target, value: e.actual })),
      source: `${fc.provenance.source_name} · ${fc.provenance.dataset}`,
      citation,
    },
    {
      id: `forecast-${model.key}`,
      name: `${model.name}, forecast ${stepUnit(fc.frequency, fc.steps)} earlier`,
      unit: fc.unit,
      points: errors.map((e) => ({ period: e.target, value: e.forecast })),
      citation: `MacroPulse ${fc.version} rolling-origin backtest`,
    },
  ];
}

function csvCell(value: string | number | null | undefined): string {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/** Self-describing CSV: every row carries unit, origin, model version and source. */
export function forecastToCsv(fc: ForecastResponse, model: ForecastModel): string {
  const source = `${fc.provenance.source_name} ${fc.provenance.dataset} (${fc.provenance.series_key}); retrieved ${fc.provenance.retrieved_at ?? "unknown"}`;
  const head = ["period", "type", "model", "step", "value", "lower_80", "upper_80", "unit", "forecast_origin", "version", "source"];
  const common = [fc.unit, fc.origin, fc.version, source];
  const rows: (string | number | null | undefined)[][] = [
    ...fc.actuals.map((a) => [a.period, "published", "", "", a.value, "", "", ...common]),
    ...model.path.map((p) => [p.period, "forecast", model.key, p.step, p.value, p.lower, p.upper, ...common]),
    ...fc.realised.map((r) => [r.period, "published_after_origin", "", "", r.value, "", "", ...common]),
  ];
  return `${[head, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n")}\r\n`;
}
