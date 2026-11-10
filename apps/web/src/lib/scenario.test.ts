import { describe, expect, it } from "vitest";

import type { ScenarioResult, ShockSpec } from "@macropulse/shared-types";

import {
  describeShocks,
  formatDeltaPp,
  loadSaved,
  MAX_SAVED,
  parseShocks,
  scenarioExport,
  serializeShocks,
  storeSaved,
  toRequestShocks,
  toSaved,
  withinSpec,
} from "@/lib/scenario";

const spec: ShockSpec[] = [
  { key: "gdp", label: "Real GDP growth", unit: "pp", minimum: -5, maximum: 5, step: 0.1, effect: "" },
  { key: "policy_rate", label: "Policy rate", unit: "pp", minimum: -4, maximum: 4, step: 0.05, effect: "" },
];

describe("shock URL encoding", () => {
  it("round-trips non-zero shocks in spec order", () => {
    const shocks = parseShocks("policy_rate:1.25,gdp:-1.5");
    expect(shocks).toEqual({ policy_rate: 1.25, gdp: -1.5 });
    expect(serializeShocks(shocks, spec)).toBe("gdp:-1.5,policy_rate:1.25");
    expect(serializeShocks({ gdp: 0 }, spec)).toBeNull();
  });

  it("drops malformed parts instead of guessing", () => {
    expect(parseShocks("gdp:abc,Oil:1,policy_rate:,:2,unemployment:2")).toEqual({ unemployment: 2 });
    expect(parseShocks(null)).toEqual({});
  });

  it("clamps to bounds, snaps to the step and forgets unknown keys", () => {
    expect(withinSpec({ gdp: -9, policy_rate: 1.234, unemployment: 2 }, spec)).toEqual({ gdp: -5, policy_rate: 1.25 });
    expect(withinSpec({ gdp: 0.30000000000000004 }, spec)).toEqual({ gdp: 0.3 });
  });

  it("describes shocks in words and formats probability changes in points", () => {
    expect(describeShocks({ gdp: -1 }, spec)).toBe("Real GDP growth -1 pp");
    expect(describeShocks({}, spec)).toBe("No shock (baseline)");
    expect(formatDeltaPp(0.1234)).toBe("+12.3 pp");
    expect(formatDeltaPp(0)).toBe("0.0 pp");
  });
});

const result = {
  baseline: { probability: 0.18, band: "moderate" },
  scenario: { probability: 0.42, band: "elevated" },
  model: { id: "run-h4-logistic", name: "Logistic Regression", run_id: "run" },
  disclaimer: "Exploratory model sensitivity analysis, not a causal economic simulation.",
} as unknown as ScenarioResult;
const request = { country: "DE", horizon: 4, as_of: null, shocks: toRequestShocks({ gdp: -1 }) };

class MemoryStorage {
  data = new Map<string, string>();
  getItem(k: string) {
    return this.data.get(k) ?? null;
  }
  setItem(k: string, v: string) {
    this.data.set(k, v);
  }
}

describe("saved scenarios", () => {
  it("stores and reloads in this browser only, capped", () => {
    const storage = new MemoryStorage();
    const items = Array.from({ length: MAX_SAVED + 3 }, (_, i) => toSaved(result, request, `s${i}`, new Date(2026, 10, 10, 0, i)));
    expect(storeSaved(items, storage)).toBe(true);
    const back = loadSaved(storage);
    expect(back).toHaveLength(MAX_SAVED);
    expect(back[0]?.scenario).toBe(0.42);
    expect(back[0]?.modelId).toBe("run-h4-logistic");
  });

  it("survives corrupt or unavailable storage", () => {
    const storage = new MemoryStorage();
    storage.setItem("macropulse.scenarios.v1", "{not json");
    expect(loadSaved(storage)).toEqual([]);
    storage.setItem("macropulse.scenarios.v1", JSON.stringify([{ id: 1 }, "x"]));
    expect(loadSaved(storage)).toEqual([]);
    const broken = { getItem: () => { throw new Error("denied"); }, setItem: () => { throw new Error("denied"); } };
    expect(loadSaved(broken)).toEqual([]);
    expect(storeSaved([], broken)).toBe(false);
  });

  it("exports the request, result and disclaimer as JSON", () => {
    const parsed = JSON.parse(scenarioExport(result, request, new Date("2026-11-10T12:00:00Z")));
    expect(parsed.kind).toBe("macropulse.scenario");
    expect(parsed.disclaimer).toContain("not a causal economic simulation");
    expect(parsed.request.shocks).toEqual({ gdp: -1, inflation: 0, unemployment: 0, policy_rate: 0, long_rate: 0 });
    expect(parsed.exported_at).toBe("2026-11-10T12:00:00.000Z");
  });
});
