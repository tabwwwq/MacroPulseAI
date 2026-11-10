import { describe, expect, it } from "vitest";

import type { Replay } from "@macropulse/shared-types";

import { gdpSeries, negativePairInWindow, quarterRange, replayMarker, VERDICTS } from "@/lib/replay";

const replay = {
  as_of: "2008-Q2",
  outcome: { status: "observed", label: 1, window: ["2008-Q3", "2008-Q4", "2009-Q1", "2009-Q2"], events: [], verdict: "miss" },
  gdp: [
    { period: "2007-Q4", value: 0.77, known_at_as_of: true },
    { period: "2008-Q1", value: 0.55, known_at_as_of: true },
    { period: "2008-Q2", value: -0.38, known_at_as_of: false },
    { period: "2008-Q3", value: -0.54, known_at_as_of: false },
    { period: "2008-Q4", value: -1.53, known_at_as_of: false },
    { period: "2009-Q1", value: -4.7, known_at_as_of: false },
    { period: "2009-Q2", value: 0.25, known_at_as_of: false },
  ],
} as unknown as Replay;

describe("quarterRange", () => {
  it("lists every quarter inclusively across years", () => {
    expect(quarterRange("2007-Q3", "2008-Q2")).toEqual(["2007-Q3", "2007-Q4", "2008-Q1", "2008-Q2"]);
    expect(quarterRange("2008-Q2", "2008-Q2")).toEqual(["2008-Q2"]);
  });

  it("returns nothing for malformed or reversed bounds", () => {
    expect(quarterRange("2008-Q3", "2008-Q1")).toEqual([]);
    expect(quarterRange("2008Q1", "2009-Q1")).toEqual([]);
  });
});

describe("replay display", () => {
  it("separates what was published by the as-of from what came later", () => {
    const [known, later] = gdpSeries(replay);
    expect(known?.points.map((p) => p.period)).toEqual(["2007-Q4", "2008-Q1"]);
    expect(later?.points.map((p) => p.period)).toEqual(["2008-Q2", "2008-Q3", "2008-Q4", "2009-Q1", "2009-Q2"]);
    expect(known?.name).toBe("Published by 2008-Q2");
  });

  it("finds a negative pair inside the outcome window only", () => {
    expect(negativePairInWindow(replay)).toBe(true);
    const calm = { ...replay, gdp: replay.gdp.map((g) => ({ ...g, value: Math.abs(g.value) })) } as Replay;
    expect(negativePairInWindow(calm)).toBe(false);
  });

  it("labels every verdict in words (never colour alone) and marks the replay date", () => {
    expect(Object.keys(VERDICTS).sort()).toEqual(["correct_quiet", "false_alarm", "hit", "miss"]);
    expect(VERDICTS.miss?.label).toBe("Missed");
    expect(replayMarker("2008-Q4")).toEqual({ from: "2008-Q4", to: "2009-Q1", label: "2008-Q4", prefix: "Replay date" });
  });
});
