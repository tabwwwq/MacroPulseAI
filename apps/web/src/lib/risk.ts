import type { RecessionHistory } from "@macropulse/shared-types";

import type { ChartSeries, ChartShading } from "@/components/charts/types";

export type BadgeTone = "ok" | "accent" | "warn" | "neutral" | "danger";

/** Text and tone for the published probability bands (never colour alone). */
export const BANDS: Record<string, { label: string; tone: BadgeTone; color: string }> = {
  low: { label: "Low", tone: "ok", color: "#3dd6a3" },
  moderate: { label: "Moderate", tone: "accent", color: "#4cc3ff" },
  elevated: { label: "Elevated", tone: "warn", color: "#f5b544" },
  high: { label: "High", tone: "danger", color: "#f2667a" },
};

const pct = new Intl.NumberFormat("en-GB", { style: "percent", maximumFractionDigits: 1, minimumFractionDigits: 1 });
const num = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 3, minimumFractionDigits: 3, signDisplay: "exceptZero" });

export function formatProbability(p: number | null | undefined): string {
  return typeof p === "number" && Number.isFinite(p) ? pct.format(p) : "N/A";
}

/** Signed metric value (Brier skill, contributions) or N/A. */
export function formatSigned(v: number | null | undefined): string {
  return typeof v === "number" && Number.isFinite(v) ? num.format(v) : "N/A";
}

export function formatMetric(v: number | null | undefined, digits = 3): string {
  return typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "N/A";
}

/**
 * Risk timeline series in percent: the published model's walk-forward estimates (each from a model
 * trained only on earlier outcomes), the prevalence baseline from the same folds, and the current
 * estimate as its own series so it is never mistaken for a backtest value.
 */
export function timelineSeries(history: RecessionHistory, modelLabel: string): ChartSeries[] {
  const toPct = (p: number) => Math.round(p * 10000) / 100;
  const oos = history.points.filter((p) => p.split !== "live");
  const live = history.points.filter((p) => p.split === "live");
  const series: ChartSeries[] = [
    {
      id: "walk-forward",
      name: `${modelLabel} · walk-forward`,
      unit: "%",
      points: oos.map((p) => ({ period: p.as_of, value: toPct(p.probability) })),
      citation: `MacroPulse model ${history.model_id}; out-of-sample walk-forward estimates`,
    },
    {
      id: "baseline",
      name: "Prevalence baseline",
      unit: "%",
      points: history.baseline.map((p) => ({ period: p.as_of, value: toPct(p.probability) })),
      citation: `Training event rate of each walk-forward fold (${history.model_id} run)`,
    },
  ];
  if (live.length) {
    series.push({
      id: "current",
      name: "Current estimate",
      unit: "%",
      points: live.map((p) => ({ period: p.as_of, value: toPct(p.probability) })),
      citation: `MacroPulse model ${history.model_id}; published model, latest as-of`,
    });
  }
  return series;
}

export function recessionShading(history: RecessionHistory): ChartShading[] {
  const first = history.points[0]?.as_of ?? "";
  return history.recessions
    .filter((r) => r.end >= first)
    .map((r) => ({ from: r.start, to: r.end, label: "technical recession (stored GDP)", prefix: "Realised" }));
}

/**
 * A recession within 2 quarters is also within 4, so P(4Q) >= P(2Q) must hold. The two horizons are
 * separate models and can violate this; the UI says so instead of silently adjusting either number.
 */
export function horizonConflict(p2: number | null | undefined, p4: number | null | undefined): boolean {
  return typeof p2 === "number" && typeof p4 === "number" && p4 + 1e-9 < p2;
}

export const HORIZON_CONFLICT_NOTE =
  "The 4-quarter estimate is below the 2-quarter one, which is logically impossible for the same event window: the two horizons are separate models. Treat both numbers as rough.";
