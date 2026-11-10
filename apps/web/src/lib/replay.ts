import type { Replay } from "@macropulse/shared-types";

import type { ChartSeries, ChartShading } from "@/components/charts/types";
import type { BadgeTone } from "@/lib/risk";

/** Shown when no as-of is selected: the best-known stress test for a recession model. */
export const DEFAULT_REPLAY = "2008-Q2";

const QUARTER = /^(\d{4})-Q([1-4])$/;

function ordinal(q: string): number | null {
  const m = QUARTER.exec(q);
  return m ? Number(m[1]) * 4 + Number(m[2]) - 1 : null;
}

function fromOrdinal(o: number): string {
  return `${Math.floor(o / 4)}-Q${(o % 4) + 1}`;
}

/** Every quarter from `first` to `last`, oldest first (empty when malformed or reversed). */
export function quarterRange(first: string, last: string): string[] {
  const a = ordinal(first);
  const b = ordinal(last);
  if (a === null || b === null || b < a) return [];
  return Array.from({ length: b - a + 1 }, (_, i) => fromOrdinal(a + i));
}

export const VERDICTS: Record<string, { label: string; tone: BadgeTone; text: string }> = {
  hit: { label: "Warned", tone: "ok", text: "The estimate reached the 50 % line and a technical recession followed." },
  miss: { label: "Missed", tone: "danger", text: "A technical recession followed, but the estimate stayed below 50 %." },
  false_alarm: { label: "False alarm", tone: "warn", text: "The estimate reached 50 %, but no technical recession followed." },
  correct_quiet: { label: "Correctly quiet", tone: "neutral", text: "The estimate stayed below 50 % and no technical recession followed." },
};

export const OUTCOME_PENDING = { label: "Outcome not known yet", tone: "neutral" as BadgeTone, text: "The outcome window has not been fully published." };

export const EPISODE_STATUS: Record<string, { label: string; tone: BadgeTone }> = {
  warned: { label: "Warned", tone: "ok" },
  missed: { label: "Missed", tone: "danger" },
  not_evaluable: { label: "Not evaluable", tone: "neutral" },
};

/** GDP growth known at the as-of vs published later (the outcome window), as two bar series. */
export function gdpSeries(r: Replay): ChartSeries[] {
  return [
    {
      id: "known",
      name: `Published by ${r.as_of}`,
      unit: "% q/q",
      points: r.gdp.filter((g) => g.known_at_as_of).map((g) => ({ period: g.period, value: g.value })),
      citation: "Today's revised values; publication-lag cut-off",
    },
    {
      id: "later",
      name: "Published later",
      unit: "% q/q",
      points: r.gdp.filter((g) => !g.known_at_as_of).map((g) => ({ period: g.period, value: g.value })),
      citation: "Observed after the as-of date",
      color: "#a0abc0", // neutral: "later" is a time marker, not good or bad news
    },
  ];
}

/** Marks the replay quarter on the walk-forward timeline (one quarter wide, so it is visible). */
export function replayMarker(asOf: string): ChartShading {
  const o = ordinal(asOf);
  return { from: asOf, to: o === null ? asOf : fromOrdinal(o + 1), label: asOf, prefix: "Replay date" };
}

export function negativePairInWindow(r: Replay): boolean {
  const values = r.outcome.window.map((q) => r.gdp.find((g) => g.period === q)?.value);
  return values.some((v, i) => i > 0 && typeof v === "number" && v < 0 && (values[i - 1] ?? 0) < 0);
}
