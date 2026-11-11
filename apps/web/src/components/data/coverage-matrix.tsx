"use client";

import Link from "next/link";

import type { MappingStatus } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { cn } from "@/lib/cn";
import { availabilityReason, MAPPING_STATUS } from "@/lib/mapping";
import { useCatalog } from "@/lib/queries";

const CELL: Record<MappingStatus, string> = {
  verified: "bg-ok/15 text-ok border-ok/30",
  partial: "bg-accent/10 text-accent border-accent/30",
  stale: "bg-warn/15 text-warn border-warn/40",
  not_published: "bg-surface-2 text-fg-subtle border-line-strong border-dashed",
  unmapped: "bg-transparent text-fg-subtle border-line border-dashed",
};
const SHORT: Record<MappingStatus, string> = {
  verified: "✓ verified",
  partial: "◐ partial",
  stale: "! stale",
  not_published: "– n/p",
  unmapped: "· none",
};

/**
 * Country × indicator availability from the live source probe, plus stored-observation counts.
 * Text symbols + labels carry the meaning (not colour alone); cells link to the country data tab.
 */
export function CoverageMatrix() {
  const catalog = useCatalog(null);

  if (catalog.isPending) return <Skeleton className="h-72 w-full" />;
  if (catalog.isError) return <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} />;

  const countries = catalog.data.countries;
  const indicators = countries[0]?.items.map((e) => e.indicator) ?? [];

  return (
    <div>
      <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
        <table className="w-full min-w-[720px] border-separate border-spacing-1 text-left text-xs">
          <caption className="sr-only">Data availability by country and indicator (probe {catalog.data.probe_date})</caption>
          <thead>
            <tr className="text-fg-subtle">
              <th scope="col" className="p-1 font-medium">Indicator</th>
              {countries.map((c) => (
                <th key={c.country} scope="col" className="p-1 text-center font-mono font-medium">
                  {c.country}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {indicators.map((ind) => (
              <tr key={ind.id}>
                <th scope="row" className="whitespace-nowrap p-1 pr-3 text-sm font-normal text-fg-muted">
                  {ind.name}
                </th>
                {countries.map((c) => {
                  const entry = c.items.find((e) => e.indicator.id === ind.id);
                  if (!entry) return <td key={c.country} />;
                  const status = entry.mapping.status;
                  return (
                    <td key={c.country} className="p-0">
                      <Link
                        href={`/countries/${c.country.toLowerCase()}?tab=data`}
                        title={`${c.country} · ${ind.name}: ${availabilityReason(entry)}`}
                        className={cn(
                          "flex h-9 flex-col items-center justify-center rounded-md border font-mono leading-tight hover:brightness-125",
                          CELL[status],
                        )}
                      >
                        <span>{SHORT[status]}</span>
                        <span className="sr-only">
                          {MAPPING_STATUS[status].label}. {entry.ingestion.observations} observations stored.
                        </span>
                      </Link>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-fg-muted">
        {(Object.keys(MAPPING_STATUS) as MappingStatus[]).map((s) => (
          <Badge key={s} tone={MAPPING_STATUS[s].tone} dashed={MAPPING_STATUS[s].tone === "neutral"}>
            {SHORT[s]} = {MAPPING_STATUS[s].label}
          </Badge>
        ))}
        <span>· Status is what the live probe found; hover a cell for the observations actually stored.</span>
      </div>
    </div>
  );
}
