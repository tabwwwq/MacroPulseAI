"use client";

import { FlaskConical } from "lucide-react";

import type { SourceStatus } from "@macropulse/shared-types";

import { useSourcesStatus } from "@/lib/queries";
import { useHydrated } from "@/lib/use-hydrated";

/** Capture date of the snapshot in use, when any source's current data came from a snapshot. */
export function demoSnapshotDate(items: SourceStatus[] | undefined): string | null {
  const stamps = (items ?? [])
    .filter((s) => s.data_mode === "snapshot" && s.snapshot_taken_at)
    .map((s) => s.snapshot_taken_at as string)
    .sort();
  return stamps.at(-1)?.slice(0, 10) ?? null;
}

/** Prominent, always-visible notice while the app runs on the bundled demo snapshot. */
export function DemoBanner() {
  const hydrated = useHydrated();
  const sources = useSourcesStatus();
  const date = hydrated ? demoSnapshotDate(sources.data?.items) : null;
  if (!date) return null;
  return (
    <div role="note" className="border-b border-warn/40 bg-warn/[0.12] px-4 py-2 text-sm text-fg sm:px-6 lg:px-8">
      <p className="mx-auto flex max-w-7xl items-start gap-2">
        <FlaskConical className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
        <span>
          <strong className="font-semibold">Demo data.</strong> A snapshot of official statistics captured on {date}{" "}
          (Eurostat, ECB, FRED), loaded offline. It is not updated: run{" "}
          <code className="font-mono text-xs">pnpm data:sync</code> on the server for current data.
        </span>
      </p>
    </div>
  );
}
