export interface SeriesPoint {
  period: string;
  value: number | null;
}

export interface ChartSeries {
  id: string;
  name: string;
  unit: string;
  points: SeriesPoint[];
}

export interface ChartShading {
  from: string;
  to: string;
  label: string;
}

export interface ChartSource {
  label: string;
  href?: string;
  retrievedAt?: string | null;
}

export type ChartKind = "line" | "bar";
