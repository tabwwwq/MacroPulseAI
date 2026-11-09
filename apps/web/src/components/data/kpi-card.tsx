import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";

export interface KpiCardProps {
  label: string;
  unit?: string;
  /** Measured value. `null`/`undefined` renders an explicit unavailable state — never a placeholder number. */
  value?: number | null;
  period?: string | null;
  isLoading?: boolean;
  /** Small status badge (source status, model state, …). */
  badge?: { label: string; tone: "ok" | "accent" | "warn" | "neutral" | "danger" };
  /** Why the value is missing or what it means. */
  note?: ReactNode;
  /** Source line, e.g. "Eurostat · namq_10_gdp". */
  source?: string | null;
  /** Marks a value older than expected for its release cycle. */
  stale?: boolean;
  className?: string;
}

const numberFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2, minimumFractionDigits: 1 });

export function KpiCard({ label, unit, value, period, isLoading, badge, note, source, stale, className }: KpiCardProps) {
  const hasValue = typeof value === "number" && Number.isFinite(value);
  return (
    <article
      className={cn(
        "flex min-w-0 flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-card",
        stale && "border-warn/40",
        className,
      )}
      aria-busy={isLoading || undefined}
    >
      <header className="flex items-start justify-between gap-2">
        <h3 className="text-xs font-medium uppercase tracking-wider text-fg-subtle">{label}</h3>
        {badge ? (
          <Badge tone={badge.tone} dashed={badge.tone === "neutral"} className="shrink-0">
            {badge.label}
          </Badge>
        ) : null}
      </header>

      {isLoading ? (
        <Skeleton className="h-8 w-24" />
      ) : (
        <p className="flex items-baseline gap-1.5">
          {hasValue ? (
            <>
              <span className="tabular font-mono text-2xl font-semibold text-fg">{numberFormat.format(value)}</span>
              {unit ? <span className="text-sm text-fg-muted">{unit}</span> : null}
            </>
          ) : (
            <>
              <span className="font-mono text-2xl font-semibold text-fg-subtle" aria-hidden>
                —
              </span>
              <span className="sr-only">No value available.</span>
            </>
          )}
          {hasValue && stale ? (
            <Badge tone="warn" className="ml-auto">
              Stale
            </Badge>
          ) : null}
        </p>
      )}

      {period && hasValue ? <p className="font-mono text-xs text-fg-subtle">{period}</p> : null}
      {note ? <p className="text-xs leading-relaxed text-fg-muted">{note}</p> : null}
      {source ? <p className="mt-auto truncate font-mono text-[11px] text-fg-subtle" title={source}>{source}</p> : null}
    </article>
  );
}
