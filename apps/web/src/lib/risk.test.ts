import { describe, expect, it } from "vitest";

import type { RecessionHistory } from "@macropulse/shared-types";

import { formatProbability, formatSigned, horizonConflict, recessionShading, timelineSeries } from "@/lib/risk";

const history: RecessionHistory = {
  country: "DE",
  horizon: 4,
  model_id: "20261109T182857Z-h4-logistic",
  model_name: "Logistic Regression",
  points: [
    { as_of: "2007-Q4", probability: 0.12, label: 1, split: "development", fold_year: 2007 },
    { as_of: "2016-Q1", probability: 0.3, label: 0, split: "heldout", fold_year: 2016 },
    { as_of: "2026-Q2", probability: 0.2, label: null, split: "unlabelled", fold_year: 2026 },
    { as_of: "2026-Q3", probability: 0.183, label: null, split: "live", fold_year: null },
  ],
  baseline: [{ as_of: "2007-Q4", probability: 0.15, label: 1, split: "development", fold_year: 2007 }],
  recessions: [
    { start: "1992-Q2", end: "1993-Q1" },
    { start: "2008-Q2", end: "2009-Q1" },
  ],
  note: "",
};

describe("timelineSeries", () => {
  it("keeps walk-forward, baseline and the current estimate apart, in percent", () => {
    const [wf, base, current] = timelineSeries(history, "Logistic Regression");
    expect(wf?.points.map((p) => p.period)).toEqual(["2007-Q4", "2016-Q1", "2026-Q2"]);
    expect(wf?.points[0]?.value).toBe(12);
    expect(base?.name).toBe("Prevalence baseline");
    expect(current?.name).toBe("Current estimate");
    expect(current?.points).toEqual([{ period: "2026-Q3", value: 18.3 }]);
  });
});

describe("recessionShading", () => {
  it("shades realised technical recessions that overlap the timeline, labelled as realised", () => {
    const shading = recessionShading(history);
    expect(shading).toEqual([{ from: "2008-Q2", to: "2009-Q1", label: "technical recession (stored GDP)", prefix: "Realised" }]);
  });
});

describe("horizonConflict", () => {
  it("flags a 4-quarter estimate below the 2-quarter one", () => {
    expect(horizonConflict(0.209, 0.142)).toBe(true);
    expect(horizonConflict(0.04, 0.18)).toBe(false);
    expect(horizonConflict(0.1, 0.1)).toBe(false);
    expect(horizonConflict(null, 0.1)).toBe(false);
  });
});

describe("formatting", () => {
  it("never prints a number for a missing value", () => {
    expect(formatProbability(0.1834)).toBe("18.3%");
    expect(formatProbability(null)).toBe("N/A");
    expect(formatSigned(-0.448)).toBe("-0.448");
    expect(formatSigned(0.099)).toBe("+0.099");
    expect(formatSigned(undefined)).toBe("N/A");
  });
});
