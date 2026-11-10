import type { ScenarioRequest, ScenarioResult, ScenarioShocks, ShockSpec } from "@macropulse/shared-types";

export type Shocks = Record<string, number>;

const KEY = /^[a-z_]{2,20}$/;
const STORAGE_KEY = "macropulse.scenarios.v1";
export const MAX_SAVED = 20;

/** `?s=gdp:-1.5,unemployment:2` → shocks. Unknown keys and non-numbers are dropped; bounds are
 *  enforced by `withinSpec` (and again by the API). */
export function parseShocks(param: string | null): Shocks {
  const out: Shocks = {};
  for (const part of (param ?? "").split(",")) {
    const [key, raw] = part.split(":");
    const value = Number(raw);
    if (key && KEY.test(key) && raw !== undefined && raw.trim() !== "" && Number.isFinite(value)) out[key] = value;
  }
  return out;
}

/** Non-zero shocks only, in spec order; null when nothing is shocked. */
export function serializeShocks(shocks: Shocks, spec: ShockSpec[]): string | null {
  const parts = spec.filter((s) => (shocks[s.key] ?? 0) !== 0).map((s) => `${s.key}:${round(shocks[s.key] ?? 0, s.step)}`);
  return parts.length ? parts.join(",") : null;
}

function decimals(step: number): number {
  const text = String(step);
  return text.includes(".") ? (text.split(".")[1]?.length ?? 0) : 0;
}

function round(value: number, step: number): number {
  return Number((Math.round(value / step) * step).toFixed(decimals(step)));
}

/** Keep only known shocks, clamped to their bounds and snapped to their step. */
export function withinSpec(shocks: Shocks, spec: ShockSpec[]): Shocks {
  const out: Shocks = {};
  for (const s of spec) {
    const v = shocks[s.key];
    if (typeof v !== "number" || !Number.isFinite(v) || v === 0) continue;
    out[s.key] = round(Math.min(s.maximum, Math.max(s.minimum, v)), s.step);
  }
  return out;
}

/** The typed request body: every shock the API defines, zero when not set. */
export function toRequestShocks(shocks: Shocks): ScenarioShocks {
  const v = (k: string) => shocks[k] ?? 0;
  return { gdp: v("gdp"), inflation: v("inflation"), unemployment: v("unemployment"), policy_rate: v("policy_rate"), long_rate: v("long_rate") };
}

export function isUnshocked(shocks: Shocks): boolean {
  return Object.values(shocks).every((v) => v === 0);
}

const signed = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2, signDisplay: "exceptZero" });
const pp = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1, minimumFractionDigits: 1, signDisplay: "exceptZero" });

export function formatShock(value: number, unit: string): string {
  return `${signed.format(value)} ${unit}`;
}

/** Difference of two probabilities in percentage points. */
export function formatDeltaPp(delta: number): string {
  return `${pp.format(delta * 100)} pp`;
}

export function describeShocks(shocks: Shocks, spec: ShockSpec[]): string {
  const parts = spec.filter((s) => (shocks[s.key] ?? 0) !== 0).map((s) => `${s.label} ${formatShock(shocks[s.key] ?? 0, s.unit)}`);
  return parts.length ? parts.join(", ") : "No shock (baseline)";
}

export interface SavedScenario {
  id: string;
  name: string;
  savedAt: string;
  request: ScenarioRequest;
  baseline: number;
  scenario: number;
  modelId: string;
}

function isSaved(value: unknown): value is SavedScenario {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Partial<SavedScenario>;
  return typeof v.id === "string" && typeof v.name === "string" && typeof v.request === "object" && v.request !== null &&
    typeof v.scenario === "number" && typeof v.baseline === "number";
}

/** Saved scenarios live only in this browser; storage may be unavailable (private mode). */
export function loadSaved(storage: Pick<Storage, "getItem"> | undefined = globalThis.localStorage): SavedScenario[] {
  try {
    const raw = storage?.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter(isSaved).slice(0, MAX_SAVED) : [];
  } catch {
    return [];
  }
}

export function storeSaved(list: SavedScenario[], storage: Pick<Storage, "setItem"> | undefined = globalThis.localStorage): boolean {
  try {
    storage?.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_SAVED)));
    return storage !== undefined;
  } catch {
    return false;
  }
}

export function toSaved(result: ScenarioResult, request: ScenarioRequest, name: string, now = new Date()): SavedScenario {
  return {
    id: `${now.getTime().toString(36)}-${Math.round(result.scenario.probability * 1e6).toString(36)}`,
    name,
    savedAt: now.toISOString(),
    request,
    baseline: result.baseline.probability,
    scenario: result.scenario.probability,
    modelId: result.model.id ?? "unknown",
  };
}

/** Full JSON export: request, every input and contribution, warnings and the disclaimer. */
export function scenarioExport(result: ScenarioResult, request: ScenarioRequest, now = new Date()): string {
  return `${JSON.stringify({ kind: "macropulse.scenario", exported_at: now.toISOString(), disclaimer: result.disclaimer, request, result }, null, 2)}\n`;
}
