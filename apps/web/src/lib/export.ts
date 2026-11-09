import type { ChartSeries } from "@/components/charts/types";

/** One alignment for the chart, accessible table and CSV. Missing values stay missing. */
export function alignSeries(series: ChartSeries[]) {
  const periods = [...new Set(series.flatMap(({ points }) => points.map(({ period }) => period)))].sort();
  const columns = series.map(({ name, unit, points }) => {
    const byPeriod = new Map(points.map(({ period, value }) => [period, value]));
    return {
      label: unit ? `${name} (${unit})` : name,
      values: periods.map((period) => {
        const value = byPeriod.get(period);
        return typeof value === "number" && Number.isFinite(value) ? value : null;
      }),
    };
  });
  return { periods, columns };
}

function csvCell(value: string | number | null): string {
  const text = value === null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/**
 * RFC 4180 records, including CRLF line endings, units in each series header and, when known, the
 * series citation (source and retrieval date) in brackets, so an exported file still says where
 * every column comes from.
 */
export function seriesToCsv(series: ChartSeries[]): string {
  const { periods, columns } = alignSeries(series);
  const rows = [
    ["period", ...columns.map(({ label }, i) => (series[i]?.citation ? `${label} [${series[i].citation}]` : label))],
    ...periods.map((period, index) => [period, ...columns.map(({ values }) => values[index] ?? null)]),
  ];
  return `${rows.map((row) => row.map(csvCell).join(",")).join("\r\n")}\r\n`;
}

export function downloadText(filename: string, text: string, mime = "text/csv;charset=utf-8"): void {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  try {
    downloadDataUrl(filename, url);
  } finally {
    // Allow the browser to start consuming the object URL before releasing it.
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export function downloadDataUrl(filename: string, dataUrl: string): void {
  const anchor = document.createElement("a");
  anchor.href = dataUrl;
  anchor.download = filename;
  anchor.hidden = true;
  document.body.appendChild(anchor);
  try {
    anchor.click();
  } finally {
    anchor.remove();
  }
}
