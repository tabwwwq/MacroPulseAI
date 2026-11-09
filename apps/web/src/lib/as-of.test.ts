import { describe, expect, it } from "vitest";

import {
  AS_OF_MIN,
  currentQuarter,
  formatAsOf,
  isValidAsOf,
  parseQuarter,
  quarterEndDate,
  selectableQuarters,
} from "@/lib/as-of";

const NOW = new Date("2026-11-09T12:00:00Z");

describe("as-of quarters", () => {
  it("parses only well-formed quarters", () => {
    expect(parseQuarter("2008-Q3")).toEqual({ year: 2008, q: 3 });
    expect(parseQuarter("2008-Q5")).toBeNull();
    expect(parseQuarter("2008Q3")).toBeNull();
    expect(parseQuarter(null)).toBeNull();
  });

  it("knows the current quarter in UTC", () => {
    expect(currentQuarter(NOW)).toBe("2026-Q4");
    expect(currentQuarter(new Date("2026-03-31T23:59:59Z"))).toBe("2026-Q1");
  });

  it("rejects quarters outside the supported window", () => {
    expect(isValidAsOf("2008-Q3", NOW)).toBe(true);
    expect(isValidAsOf(AS_OF_MIN, NOW)).toBe(true);
    expect(isValidAsOf("1994-Q4", NOW)).toBe(false);
    expect(isValidAsOf("2027-Q1", NOW)).toBe(false); // future information sets are not allowed
    expect(isValidAsOf("garbage", NOW)).toBe(false);
  });

  it("lists quarters newest first, bounded on both sides", () => {
    const qs = selectableQuarters(NOW);
    expect(qs[0]).toBe("2026-Q4");
    expect(qs.at(-1)).toBe(AS_OF_MIN);
    expect(qs).toHaveLength((2026 - 1995) * 4 + 4);
  });

  it("formats and resolves quarter end dates", () => {
    expect(quarterEndDate("2008-Q3")).toBe("2008-09-30");
    expect(quarterEndDate("2024-Q1")).toBe("2024-03-31");
    expect(formatAsOf("2008-Q3")).toBe("Q3 2008");
    expect(formatAsOf(null)).toBe("Latest");
  });
});
