"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import { ArrowDownRight, ArrowRight, ArrowUpRight, Info } from "lucide-react";
import type { ReactNode } from "react";

import { Sparkline } from "@/components/charts/sparkline";
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
  /** Change versus the previous observation, in `changeUnit`. */
  change?: number | null;
  changeUnit?: string;
  previousPeriod?: string | null;
  /** Source observation flag in words ("provisional", "estimated"). */
  flag?: string | null;
  /** Provenance details shown in an accessible tooltip (hover or keyboard focus). */
  provenance?: ReactNode;
  /** Recent stored observations, oldest → newest, drawn as a sparkline. Gaps stay gaps. */
  trend?: { values: (number | null)[]; label: string };
  className?: string;
}

const numberFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2, minimumFractionDigits: 1 });
const changeFormat = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
  signDisplay: "exceptZero",
});

function Change({ change, unit, previous }: { change: number; unit?: string; previous?: string | null }) {
  const rounded = Math.round(change * 100) / 100;
  const Icon = rounded > 0 ? ArrowUpRight : rounded < 0 ? ArrowDownRight : ArrowRight;
  const word = rounded > 0 ? "up" : rounded < 0 ? "down" : "unchanged";
  return (
    <p className="flex min-w-0 items-center gap-2 font-mono text-xs text-fg-muted">
      {/* Direction only: whether "up" is good depends on the indicator, so the chip stays neutral. */}
      <span className="inline-flex shrink-0 items-center gap-1 rounded-md border border-line-strong bg-canvas/60 px-1.5 py-0.5 text-fg">
        <Icon className="size-3.5 shrink-0 text-accent" aria-hidden />
        <span className="sr-only">{word}</span>
        <span className="tabular">
          {changeFormat.format(rounded)}
          {unit ? ` ${unit}` : ""}
        </span>
      </span>
      {previous ? <span className="truncate text-fg-subtle">vs {previous}</span> : null}
    </p>
  );
}

export function KpiCard({
  label,
  unit,
  value,
  period,
  isLoading,
  badge,
  note,
  source,
  stale,
  change,
  changeUnit,
  previousPeriod,
  flag,
  provenance,
  trend,
  className,
}: KpiCardProps) {
  const hasValue = typeof value === "number" && Number.isFinite(value);
  return (
    <article
      className={cn(
        "panel panel-hover group flex min-w-0 flex-col gap-3 overflow-hidden p-4",
        stale && "outline outline-1 -outline-offset-1 outline-warn/40",
        className,
      )}
      aria-busy={isLoading || undefined}
      aria-label={label}
    >
      <span
        aria-hidden
        className="absolute inset-x-4 top-0 h-px bg-gradient-to-r from-transparent via-accent/70 to-transparent opacity-60 transition-opacity duration-300 group-hover:opacity-100"
      />
      <header className="flex items-start justify-between gap-2">
        <h3 className="text-[11px] font-medium uppercase tracking-[0.12em] text-fg-subtle">{label}</h3>
        {badge ? (
          <Badge tone={badge.tone} dashed={badge.tone === "neutral"} className="shrink-0">
            {badge.label}
          </Badge>
        ) : null}
      </header>

      {isLoading ? (
        <Skeleton className="h-8 w-24" />
      ) : (
        <div className="flex flex-col gap-1.5">
          <p className="flex items-baseline gap-1.5">
            {hasValue ? (
              <>
                <span className="tabular font-mono text-[28px] font-semibold leading-none tracking-tight text-fg">
                  {numberFormat.format(value)}
                </span>
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
          {hasValue && typeof change === "number" && Number.isFinite(change) ? (
            <Change change={change} unit={changeUnit} previous={previousPeriod} />
          ) : null}
        </div>
      )}

      {hasValue && trend ? (
        <Sparkline values={trend.values} ariaLabel={trend.label} className="h-9 w-full" />
      ) : null}
      {period && hasValue ? (
        <p className="flex flex-wrap items-center gap-2 font-mono text-xs text-fg-subtle">
          {period}
          {flag ? (
            <Badge tone="neutral" dashed>
              {flag}
            </Badge>
          ) : null}
        </p>
      ) : null}
      {note ? <p className="text-xs leading-relaxed text-fg-muted">{note}</p> : null}
      {source ? (
        <div className="mt-auto flex min-w-0 items-center gap-1.5">
          <p className="truncate font-mono text-[11px] text-fg-subtle" title={source}>
            {source}
          </p>
          {provenance ? (
            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button
                  type="button"
                  className="shrink-0 rounded text-fg-subtle hover:text-accent focus-visible:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
                  aria-label={`Provenance of ${label}`}
                >
                  <Info className="size-3.5" aria-hidden />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  side="top"
                  align="end"
                  sideOffset={6}
                  collisionPadding={12}
                  className="z-50 max-w-[22rem] rounded-lg border border-line-strong bg-elevated px-3 py-2.5 text-xs leading-relaxed text-fg-muted shadow-card"
                >
                  {provenance}
                  <Tooltip.Arrow className="fill-elevated" />
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
