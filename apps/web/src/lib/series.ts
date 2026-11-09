import type { IndicatorSeries, SeriesProvenance } from "@macropulse/shared-types";

import type { ChartSeries, ChartShading } from "@/components/charts/types";
import { parseQuarter } from "@/lib/as-of";

/** Visible history window. Kept in the URL as `?range=`. */
export const RANGES = [
  { value: "5y", label: "5Y", years: 5 },
  { value: "10y", label: "10Y", years: 10 },
  { value: "20y", label: "20Y", years: 20 },
  { value: "max", label: "Max", years: null },
] as const;
export type RangeKey = (typeof RANGES)[number]["value"];
export const DEFAULT_RANGE: RangeKey = "10y";

export function parseRange(value: string | null): RangeKey {
  return RANGES.some((r) => r.value === value) ? (value as RangeKey) : DEFAULT_RANGE;
}

/**
 * API period bounds for a range ending at the as-of quarter (or now). `start` is a year label, so
 * the window covers whole years; `end` is the as-of quarter, so nothing after the cut-off is drawn.
 */
export function rangeBounds(range: RangeKey, asOf: string | null, now: Date = new Date()): { start?: string; end?: string } {
  const years = RANGES.find((r) => r.value === range)?.years ?? null;
  const endYear = parseQuarter(asOf)?.year ?? now.getUTCFullYear();
  return {
    ...(years ? { start: String(endYear - years + 1) } : {}),
    ...(asOf ? { end: asOf } : {}),
  };
}

/** Short source line, e.g. "Eurostat · namq_10_gdp". */
export function provenanceLabel(p: SeriesProvenance): string {
  const publisher = p.source_id === "fred" ? "FRED" : p.source_id === "ecb" ? "ECB" : p.source_name.split(" ")[0];
  return `${publisher} · ${p.dataset}`;
}

/** API series → chart series. Event-dated series (ECB decisions) are drawn as steps. */
export function toChartSeries(s: IndicatorSeries, name?: string): ChartSeries {
  return {
    id: `${s.country}-${s.indicator.id}`,
    name: name ?? s.indicator.name,
    unit: s.unit,
    points: s.points.map(({ period, value }) => ({ period, value })),
    source: provenanceLabel(s.provenance),
    citation: `${s.provenance.source_name}, ${s.provenance.dataset} ${s.provenance.series_key}; ${s.transform}${
      s.provenance.retrieved_at ? ` Retrieved ${s.provenance.retrieved_at.slice(0, 10)}` : ""
    }`,
    step: s.indicator.frequency === "event",
  };
}

/**
 * Contiguous runs of 1 in a 0/1 reference series (FRED `USREC`), as shaded ranges. The label says
 * explicitly that this is the NBER reference chronology, not the GDP-based technical-recession target.
 */
export function referenceShading(points: { period: string; value: number }[], label = "NBER recession (FRED USREC)"): ChartShading[] {
  const out: ChartShading[] = [];
  let from: string | null = null;
  let last: string | null = null;
  for (const { period, value } of points) {
    if (value === 1) {
      from ??= period;
      last = period;
    } else if (from && last) {
      out.push({ from, to: last, label });
      from = null;
      last = null;
    }
  }
  if (from && last) out.push({ from, to: last, label });
  return out;
}

/** Keep only shading that overlaps the visible periods (labels compare lexicographically). */
export function clipShading(shading: ChartShading[], first: string | undefined): ChartShading[] {
  if (!first) return [];
  const start = first.slice(0, 7);
  return shading.filter(({ to }) => to.slice(0, 7) >= start);
}

/**
 * Difference of each series versus the first (baseline), on periods both actually have. Units must
 * match; the result is in percentage points. The baseline itself is not returned.
 */
export function spreadVsBaseline(series: ChartSeries[]): ChartSeries[] {
  const [base, ...rest] = series;
  if (!base) return [];
  const baseValues = new Map(base.points.map((p) => [p.period, p.value]));
  return rest.map((s) => ({
    ...s,
    id: `${s.id}-minus-${base.id}`,
    name: `${s.name} − ${base.name}`,
    unit: "pp",
    step: false,
    citation: [s.citation, base.citation].filter(Boolean).join(" MINUS "),
    points: s.points.flatMap(({ period, value }) => {
      const b = baseValues.get(period);
      return typeof b === "number" && typeof value === "number" ? [{ period, value: Math.round((value - b) * 1e6) / 1e6 }] : [];
    }),
  }));
}

/** Source observation flags (Eurostat / SDMX conventions) in words; `null` for "normal". */
export function flagLabel(flag: string | null | undefined): string | null {
  switch (flag) {
    case null:
    case undefined:
    case "":
    case "A":
      return null;
    case "p":
    case "P":
      return "provisional";
    case "e":
    case "E":
      return "estimated";
    case "b":
    case "B":
      return "break in series";
    case "d":
      return "definition differs";
    case "u":
      return "low reliability";
    case "F":
      return "forecast";
    default:
      return `source flag “${flag}”`;
  }
}
