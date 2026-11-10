export interface SeriesPoint {
  period: string;
  value: number | null;
}

export interface ChartSeries {
  id: string;
  name: string;
  unit: string;
  points: SeriesPoint[];
  /** Short provenance shown in the hover tooltip, e.g. "Eurostat · namq_10_gdp". */
  source?: string;
  /** Draw as a step line (values hold until the next observation, e.g. policy-rate decisions). */
  step?: boolean;
  /** Citation kept in CSV exports, e.g. "Eurostat · namq_10_gdp; retrieved 2026-11-09". */
  citation?: string;
  /** Fixed colour when the palette order would suggest a meaning (e.g. green for bad news). */
  color?: string;
}

export interface ChartShading {
  from: string;
  to: string;
  label: string;
  /** Legend/tooltip prefix; defaults to "External reference" (e.g. NBER dates). */
  prefix?: string;
}

export interface ChartSource {
  label: string;
  href?: string;
  retrievedAt?: string | null;
}

export type ChartKind = "line" | "bar";
