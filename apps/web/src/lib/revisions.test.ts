import { describe, expect, it } from "vitest";

import { formatSigned, largestRevisions, revisionChartSeries, signalLabel } from "@/lib/revisions";
import { REVISIONS_FIXTURE as data } from "@/lib/revisions.fixture";

describe("revisionChartSeries", () => {
  it("draws first releases and today's values for genuine first releases only, in period order", () => {
    const [first, latest] = revisionChartSeries(data);
    expect(first?.name).toBe("First release");
    expect(latest?.name).toBe("Today's data");
    // 1990-Q1 is back-filled history (first_release false) and is left out of both lines
    expect(first?.points).toEqual([
      { period: "2020-Q2", value: -9.49 },
      { period: "2022-Q1", value: -0.36 },
      { period: "2022-Q2", value: -0.23 },
      { period: "2022-Q3", value: 0.65 },
    ]);
    // a missing latest value stays a gap (null), it is not dropped or filled
    expect(latest?.points.at(-1)).toEqual({ period: "2022-Q3", value: null });
  });

  it("carries ids, unit and an ALFRED citation", () => {
    const [first, latest] = revisionChartSeries(data);
    expect(first?.id).toBe("US-real_gdp_qoq-first-release");
    expect(latest?.id).toBe("US-real_gdp_qoq-latest");
    expect(first?.unit).toBe("%");
    expect(first?.source).toBe("ALFRED · GDPC1");
    expect(first?.citation).toBe(
      "ALFRED (Federal Reserve Bank of St. Louis), GDPC1; 420 vintages 1991-12-04 to 2026-10-29; retrieved 2026-11-12",
    );
  });

  it("does not mutate the response", () => {
    const before = JSON.stringify(data);
    revisionChartSeries(data);
    largestRevisions(data);
    expect(JSON.stringify(data)).toBe(before);
  });
});

describe("largestRevisions", () => {
  it("ranks genuine first releases by absolute revision, skipping missing revisions", () => {
    expect(largestRevisions(data, 2).map((p) => p.period)).toEqual(["2020-Q2", "2022-Q2"]);
    expect(largestRevisions(data).map((p) => p.period)).toEqual(["2020-Q2", "2022-Q2", "2022-Q1"]);
  });

  it("breaks ties by period", () => {
    const base = data.points[1];
    if (!base) throw new Error("fixture");
    const tied = {
      ...data,
      points: [
        { ...base, period: "2021-Q2", revision: -0.5 },
        { ...base, period: "2021-Q1", revision: 0.5 },
      ],
    };
    expect(largestRevisions(tied).map((p) => p.period)).toEqual(["2021-Q1", "2021-Q2"]);
  });
});

describe("signalLabel", () => {
  it("names the three cases in words", () => {
    const [both, then, now] = data.technical_signals;
    if (!both || !then || !now) throw new Error("fixture");
    expect(signalLabel(both)).toEqual({ label: "Confirmed by today's data", tone: "neutral" });
    expect(signalLabel(then)).toEqual({ label: "Revised away", tone: "warn" });
    expect(signalLabel(now)).toEqual({ label: "Only visible in today's data", tone: "accent" });
  });
});

describe("formatSigned", () => {
  it("always shows the sign and two decimals; N/A for missing", () => {
    expect(formatSigned(0.137)).toBe("+0.14");
    expect(formatSigned(-0.23)).toBe("-0.23");
    expect(formatSigned(0)).toBe("0.00");
    expect(formatSigned(null)).toBe("N/A");
    expect(formatSigned(Number.NaN)).toBe("N/A");
    expect(formatSigned(1.2345, 3)).toBe("+1.235");
  });
});
