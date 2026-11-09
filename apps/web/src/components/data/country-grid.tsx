"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { SupportBadge } from "@/components/data/support-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { useCountries } from "@/lib/queries";

export function CountryGrid() {
  const { data, isPending, isError, error, refetch } = useCountries();

  if (isPending) {
    return (
      <div className="grid gap-3 sm:grid-cols-[repeat(auto-fill,minmax(15rem,1fr))]" aria-busy="true" aria-label="Loading countries">
        {Array.from({ length: 5 }, (_, i) => (
          <Skeleton key={i} className="h-[104px] rounded-xl" />
        ))}
      </div>
    );
  }
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />;

  return (
    <ul className="grid gap-3 sm:grid-cols-[repeat(auto-fill,minmax(15rem,1fr))]">
      {data.items.map((c) => (
        <li key={c.iso2}>
          <Link
            href={`/countries/${c.iso2.toLowerCase()}`}
            className="group flex h-full flex-col gap-3 rounded-xl border border-line bg-surface-2/60 p-4 transition-colors hover:border-accent/40 hover:bg-surface-2"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <span className="grid size-9 shrink-0 place-items-center rounded-lg border border-line-strong bg-surface font-mono text-xs font-semibold text-fg">
                  {c.iso2}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-fg">{c.name}</p>
                  <p className="truncate text-xs text-fg-subtle">
                    {c.region} · {c.currency}
                  </p>
                </div>
              </div>
              <ArrowRight
                className="size-4 shrink-0 text-fg-subtle transition-transform group-hover:translate-x-0.5 group-hover:text-accent"
                aria-hidden
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <SupportBadge support={c.support} />
              <span className="text-xs text-fg-subtle">target: {c.support.target}</span>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
