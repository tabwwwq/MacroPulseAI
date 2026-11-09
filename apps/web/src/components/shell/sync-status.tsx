"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import Link from "next/link";

import { StatusDot } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelative } from "@/lib/format";
import { useReady, useSourcesStatus } from "@/lib/queries";

type Tone = "ok" | "warn" | "danger";

/**
 * Honest sync indicator: "freshness" = last successful fetch, never a "Live" badge.
 * Links to the Data observatory, where every source's status is listed.
 */
export function SyncStatus() {
  const ready = useReady();
  const sources = useSourcesStatus();

  if (ready.isPending) return <Skeleton className="h-8 w-36 rounded-full" />;

  let tone: Tone;
  let label: string;
  let detail: string;

  if (ready.isError) {
    tone = "danger";
    label = "API offline";
    detail = "The backend is not reachable. Start it with `pnpm dev` and this badge will update.";
  } else if (ready.data.status === "not_ready") {
    tone = "warn";
    label = "API not ready";
    detail = ready.data.checks.filter((c) => !c.ok).map((c) => `${c.name}: ${c.detail}`).join(" · ");
  } else if (!sources.data) {
    tone = "warn";
    label = sources.isError ? "Sources unavailable" : "Checking sources…";
    detail = "Source status could not be loaded.";
  } else {
    const total = sources.data.items.length;
    const synced = sources.data.items.filter((s) => s.last_success_at);
    const latest = synced
      .map((s) => s.last_success_at as string)
      .sort()
      .at(-1);
    if (synced.length === 0) {
      tone = "warn";
      label = "No data synced";
      detail = `0 of ${total} official sources have been fetched yet. Data connectors arrive in Phase 3.`;
    } else {
      tone = synced.length === total ? "ok" : "warn";
      label = `${synced.length}/${total} sources synced`;
      detail = `Last successful fetch ${formatRelative(latest)}. Freshness is the last successful fetch, not the observation period.`;
    }
  }

  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <Link
          href="/data"
          className="inline-flex h-8 items-center gap-2 whitespace-nowrap rounded-full border border-line-strong bg-surface-2 px-3 text-xs font-medium text-fg-muted hover:bg-elevated hover:text-fg"
        >
          <StatusDot tone={tone} pulse={tone === "danger"} />
          <span>{label}</span>
        </Link>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          side="bottom"
          align="end"
          sideOffset={8}
          className="z-50 max-w-72 rounded-lg border border-line-strong bg-elevated px-3 py-2 text-xs leading-relaxed text-fg-muted shadow-card"
        >
          {detail}
          <Tooltip.Arrow className="fill-elevated" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
