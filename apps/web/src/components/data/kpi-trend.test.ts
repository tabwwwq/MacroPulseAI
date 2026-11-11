import { describe, expect, it } from "vitest";

import { kpiTrend, TREND_POINTS } from "@/components/data/kpi-grid";

const indicator = { id: "inflation_yoy", name: "Inflation (y/y)" } as Parameters<typeof kpiTrend>[1]["indicator"];

function series(n: number): { period: string; value: number | null }[] {
  return Array.from({ length: n }, (_, i) => ({ period: `P${String(i).padStart(3, "0")}`, value: i }));
}

describe("kpiTrend", () => {
  it("ends at the KPI's own period, so the sparkline's last point is the number shown", () => {
    const points = series(10);
    const trend = kpiTrend(points, { period: "P006", indicator });
    expect(trend?.values).toEqual([0, 1, 2, 3, 4, 5, 6]);
    expect(trend?.label).toBe("Inflation (y/y): 7 stored observations from P000 to P006");
  });

  it("shows at most the latest TREND_POINTS observations", () => {
    const trend = kpiTrend(series(60), { period: "P059", indicator });
    expect(trend?.values).toHaveLength(TREND_POINTS);
    expect(trend?.values.at(-1)).toBe(59);
    expect(trend?.values[0]).toBe(60 - TREND_POINTS);
  });

  it("keeps gaps as gaps", () => {
    const points = [
      { period: "A", value: 1 },
      { period: "B", value: null },
      { period: "C", value: 3 },
    ];
    expect(kpiTrend(points, { period: "C", indicator })?.values).toEqual([1, null, 3]);
  });

  it("draws nothing when the KPI period is not in the series or there is too little history", () => {
    expect(kpiTrend(series(5), { period: "X", indicator })).toBeNull();
    expect(kpiTrend(series(5), { period: "P000", indicator })).toBeNull();
    expect(kpiTrend(undefined, { period: "P000", indicator })).toBeNull();
    expect(kpiTrend(series(5), { period: null, indicator })).toBeNull();
  });
});
