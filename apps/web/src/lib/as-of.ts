/**
 * As-of quarters ("2008-Q3"). The as-of date is the information cut-off: from Phase 5 on, every
 * estimate may use only data published by the end of that quarter. `null` means "latest available".
 */

export const AS_OF_MIN = "1995-Q1"; // earliest quarter with real GDP for all EU countries in scope

const QUARTER = /^(\d{4})-Q([1-4])$/;

export interface Quarter {
  year: number;
  q: 1 | 2 | 3 | 4;
}

export function parseQuarter(value: string | null | undefined): Quarter | null {
  const m = QUARTER.exec(value ?? "");
  if (!m) return null;
  return { year: Number(m[1]), q: Number(m[2]) as Quarter["q"] };
}

export function quarterKey({ year, q }: Quarter): string {
  return `${year}-Q${q}`;
}

function ordinal({ year, q }: Quarter): number {
  return year * 4 + (q - 1);
}

/** Quarter containing `now` (UTC). */
export function currentQuarter(now: Date = new Date()): string {
  return quarterKey({ year: now.getUTCFullYear(), q: (Math.floor(now.getUTCMonth() / 3) + 1) as Quarter["q"] });
}

/** A valid as-of is a well-formed quarter between AS_OF_MIN and the current quarter. */
export function isValidAsOf(value: string | null | undefined, now: Date = new Date()): value is string {
  const parsed = parseQuarter(value);
  const min = parseQuarter(AS_OF_MIN);
  const max = parseQuarter(currentQuarter(now));
  if (!parsed || !min || !max) return false;
  return ordinal(parsed) >= ordinal(min) && ordinal(parsed) <= ordinal(max);
}

/** All selectable quarters, newest first. */
export function selectableQuarters(now: Date = new Date()): string[] {
  const min = parseQuarter(AS_OF_MIN) as Quarter;
  const max = parseQuarter(currentQuarter(now)) as Quarter;
  const out: string[] = [];
  for (let o = ordinal(max); o >= ordinal(min); o -= 1) {
    out.push(quarterKey({ year: Math.floor(o / 4), q: ((o % 4) + 1) as Quarter["q"] }));
  }
  return out;
}

/** Last calendar day of the quarter, ISO date. */
export function quarterEndDate(value: string): string | null {
  const parsed = parseQuarter(value);
  if (!parsed) return null;
  const end = new Date(Date.UTC(parsed.year, parsed.q * 3, 0));
  return end.toISOString().slice(0, 10);
}

/** "Q3 2008" for display; "Latest" for null. */
export function formatAsOf(value: string | null): string {
  const parsed = parseQuarter(value);
  return parsed ? `Q${parsed.q} ${parsed.year}` : "Latest";
}
