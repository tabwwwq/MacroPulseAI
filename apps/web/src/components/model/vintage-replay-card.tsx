"use client";

import { History } from "lucide-react";
import type { ReactElement, ReactNode } from "react";

import type { VintageReplay } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState, Notice } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { useVintageReplay } from "@/lib/queries";
import { BANDS, formatProbability } from "@/lib/risk";

/**
 * Signed shift between the walk-forward estimate on today's revised data and the same fold model
 * scored on the figures as first published (ALFRED). `null` vintage → `null`.
 */
export function formatShift(revised: number, vintage: number | null): { text: string; words: string } | null {
  if (vintage === null) return null;
  const pp = Math.round((vintage - revised) * 1000) / 10;
  if (pp === 0) return { text: "0.0 pp", words: "No change" };
  const text = `${pp > 0 ? "+" : ""}${pp.toFixed(1)} pp`;
  return {
    text,
    words: pp > 0 ? "Higher with the figures as first published" : "Lower with the figures as first published",
  };
}

function Stat({ label, value, hint, children }: { label: string; value: string; hint?: string; children?: ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-canvas/50 px-3 py-2.5">
      <p className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-fg-subtle">{label}</p>
      <p className="tabular mt-1 font-mono text-lg font-semibold text-fg">{value}</p>
      {hint ? <p className="mt-0.5 text-[11px] text-fg-subtle">{hint}</p> : null}
      {children}
    </div>
  );
}

/** Signed 2-decimal difference, never "-0.00" or "+0.00". */
function signedDiff(v: number): string {
  const r = Math.round(v * 100) / 100;
  if (r === 0) return "0.00";
  return `${r > 0 ? "+" : ""}${r.toFixed(2)}`;
}

/** One input value: 2 decimals in one span, the period in a separate small span (omitted when null). */
function ValueCell({ value, period }: { value: number; period: string | null }) {
  return (
    <span className="tabular font-mono text-fg">
      {value.toFixed(2)}
      {period ? <span className="ml-1 text-[10px] text-fg-subtle">{period}</span> : null}
    </span>
  );
}

/** Pure details: both estimates, the shift, and the rebuilt inputs compared against today. */
export function VintageReplayDetails({ data }: { data: VintageReplay }): ReactElement {
  const shift = formatShift(data.revised_probability, data.vintage_probability);
  const fromVintage = data.inputs.filter((i) => i.from_vintage);
  const notRevised = data.inputs.filter((i) => !i.from_vintage);

  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-3">
        <div role="group" aria-label="Today's revised data">
          <Stat label="Today's revised data" value={formatProbability(data.revised_probability)} hint="stored walk-forward estimate" />
        </div>
        <div role="group" aria-label="As first published">
          <Stat label="As first published" value={formatProbability(data.vintage_probability)}>
            {data.vintage_band ? (
              <div className="mt-1.5">
                <Badge tone={BANDS[data.vintage_band]?.tone ?? "neutral"}>{BANDS[data.vintage_band]?.label ?? data.vintage_band}</Badge>
              </div>
            ) : null}
          </Stat>
        </div>
        {shift ? (
          <Stat label="Shift" value={shift.text} hint={shift.words} />
        ) : null}
      </div>

      {!data.available ? (
        <Notice>{data.reason}</Notice>
      ) : (
        <>
          <div
            className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent"
            tabIndex={0}
            role="region"
            aria-label="Table, scrolls horizontally"
          >
            <table className="w-full min-w-[560px] text-left text-xs tabular">
              <caption className="sr-only">Inputs: today&apos;s data versus first published</caption>
              <thead className="text-fg-subtle">
                <tr>
                  <th scope="col" className="py-2 pr-4 font-medium">Input</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Today&apos;s data</th>
                  <th scope="col" className="py-2 pr-4 font-medium">First published</th>
                  <th scope="col" className="py-2 font-medium">Difference</th>
                </tr>
              </thead>
              <tbody className="font-mono text-xs">
                {fromVintage.map((i) => (
                  <tr key={i.feature} className="border-t border-line/60">
                    <th scope="row" className="py-2 pr-4 font-normal text-fg">{i.label}</th>
                    <td className="py-2 pr-4">
                      <ValueCell value={i.revised_value} period={i.revised_period} />
                    </td>
                    <td className="py-2 pr-4">
                      <ValueCell value={i.vintage_value} period={i.vintage_period} />
                    </td>
                    <td className="py-2">
                      <span className="tabular font-mono text-fg">{signedDiff(i.difference)}</span>
                      {Math.abs(i.difference) >= 0.005 ? (
                        <Badge tone="warn" className="ml-2">revised</Badge>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {notRevised.length ? (
            <p className="text-xs leading-relaxed text-fg-muted">
              Not revised, identical in both: {notRevised.map((i) => i.label).join(", ")}.
            </p>
          ) : null}
        </>
      )}

      <p className="text-xs leading-relaxed text-fg-subtle">{data.note}</p>
      <p className="font-mono text-[11px] text-fg-subtle">
        Fold {data.fold_year ?? "—"} · vintage of {data.vintage_date} · archive from {data.archive_start}
      </p>
    </div>
  );
}

/**
 * Crisis time machine: the walk-forward estimate on today's revised US data next to the same fold
 * model scored on the figures as first published (ALFRED vintage of the cut-off date).
 */
export function VintageReplayCard({ iso2, horizon, asOf }: { iso2: string; horizon: 2 | 4; asOf: string }): ReactElement {
  const q = useVintageReplay(iso2, horizon, asOf);

  let body: ReactElement;
  if (q.isPending) {
    body = <Skeleton className="h-48 rounded-xl" />;
  } else if (q.isError) {
    const err = q.error;
    if (err instanceof ApiError && (err.status === 404 || err.status === 422 || err.status === 503)) {
      body = (
        <EmptyState icon={<History className="size-6" aria-hidden />} title="First-release comparison unavailable">
          {err.message}
        </EmptyState>
      );
    } else {
      body = <ErrorState error={q.error} onRetry={() => void q.refetch()} />;
    }
  } else {
    body = <VintageReplayDetails data={q.data} />;
  }

  return (
    <Card aria-busy={q.isFetching} aria-label="With the figures as first published">
      <CardHeader
        title="With the figures as first published"
        description="Same walk-forward fold model · US GDP, CPI and unemployment from the ALFRED vintage of the cut-off date"
        action={<Badge tone="accent">ALFRED vintage</Badge>}
      />
      <CardBody>{body}</CardBody>
    </Card>
  );
}
