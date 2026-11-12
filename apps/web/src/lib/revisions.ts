import type { RevisionPointOut, Revisions, TechnicalSignal } from "@macropulse/shared-types";

import type { ChartSeries } from "@/components/charts/types";

const formatterCache = new Map<number, Intl.NumberFormat>();

function getFormatter(digits: number): Intl.NumberFormat {
  let f = formatterCache.get(digits);
  if (!f) {
    f = new Intl.NumberFormat("en-GB", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
      signDisplay: "exceptZero",
    });
    formatterCache.set(digits, f);
  }
  return f;
}

export function formatSigned(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  return getFormatter(digits).format(value);
}

export function signalLabel(signal: TechnicalSignal): { label: string; tone: "neutral" | "warn" | "accent" } {
  if (signal.as_first_known && signal.in_latest_data) {
    return { label: "Confirmed by today's data", tone: "neutral" };
  }
  if (signal.as_first_known) {
    return { label: "Revised away", tone: "warn" };
  }
  if (signal.in_latest_data) {
    return { label: "Only visible in today's data", tone: "accent" };
  }
  return { label: "Not in either vintage", tone: "neutral" };
}

export function revisionChartSeries(data: Revisions): ChartSeries[] {
  const points = data.points
    .filter((p) => p.first_release)
    .map((p) => ({ ...p }))
    .sort((a, b) => (a.period < b.period ? -1 : a.period > b.period ? 1 : 0));

  const { country, indicator, series } = data;
  const unit = indicator.unit;
  const source = `ALFRED · ${series.dataset}`;
  const citation = `ALFRED (Federal Reserve Bank of St. Louis), ${series.dataset}; ${series.vintages} vintages ${series.first_vintage} to ${series.last_vintage}; retrieved ${series.retrieved_at.slice(0, 10)}`;

  const first: ChartSeries = {
    id: `${country}-${indicator.id}-first-release`,
    name: "First release",
    unit,
    points: points.map((p) => ({ period: p.period, value: p.first_value })),
    source,
    citation,
  };

  const latest: ChartSeries = {
    id: `${country}-${indicator.id}-latest`,
    name: "Today's data",
    unit,
    points: points.map((p) => ({ period: p.period, value: p.latest_value })),
    source,
    citation,
  };

  return [first, latest];
}

export function largestRevisions(data: Revisions, n = 5): RevisionPointOut[] {
  const ranked = data.points
    .filter((p): p is RevisionPointOut & { revision: number } => p.first_release && p.revision !== null)
    .map((p) => ({ ...p }))
    .sort((a, b) => {
      const diff = Math.abs(b.revision) - Math.abs(a.revision);
      if (diff !== 0) return diff;
      return a.period < b.period ? -1 : a.period > b.period ? 1 : 0;
    });
  return ranked.slice(0, n);
}
