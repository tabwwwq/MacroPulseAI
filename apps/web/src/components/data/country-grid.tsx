"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import type { Country } from "@macropulse/shared-types";

import { SupportBadge } from "@/components/data/support-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { useCountries } from "@/lib/queries";

const CARD =
  "panel panel-hover group flex h-full w-full flex-col gap-3 p-4 text-left";

function CardContent({ c }: { c: Country }): ReactNode {
  return (
    <>
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl border border-accent/25 bg-[radial-gradient(circle_at_30%_20%,rgb(76_195_255/0.28),rgb(23_34_56/0.9)_70%)] font-mono text-xs font-semibold text-fg shadow-[0_0_18px_-6px_rgb(76_195_255/0.6)]">
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
    </>
  );
}

/**
 * Supported countries. Default: links to each country profile. With `onSelect`, cards are buttons that
 * set the global country (used by the overview's guided first-use selector).
 */
export function CountryGrid({ onSelect }: { onSelect?: (iso2: string) => void }) {
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
          {onSelect ? (
            <button type="button" className={CARD} onClick={() => onSelect(c.iso2)} aria-label={`Analyse ${c.name}`}>
              <CardContent c={c} />
            </button>
          ) : (
            <Link href={`/countries/${c.iso2.toLowerCase()}`} className={CARD}>
              <CardContent c={c} />
            </Link>
          )}
        </li>
      ))}
    </ul>
  );
}
