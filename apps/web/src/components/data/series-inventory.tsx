"use client";

import { useState } from "react";

import { StoredSeriesTable } from "@/components/data/stored-series-table";
import { Badge } from "@/components/ui/badge";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { formatDateTimeUtc } from "@/lib/format";
import { useDataQuality } from "@/lib/queries";

const SOURCES = [
  { value: "all", label: "All sources" },
  { value: "eurostat", label: "Eurostat" },
  { value: "ecb", label: "ECB" },
  { value: "fred", label: "FRED" },
] as const;
type SourceFilter = (typeof SOURCES)[number]["value"];

/** Every native series the catalog maps to a connector: what is stored, from where, and its checks. */
export function SeriesInventory() {
  const quality = useDataQuality(null);
  const [source, setSource] = useState<SourceFilter>("all");

  if (quality.isError) return <ErrorState error={quality.error} onRetry={() => void quality.refetch()} />;
  if (quality.isPending) return <Skeleton className="h-64 w-full" />;

  const items = quality.data.items.filter((s) => source === "all" || s.source_id === source);
  const total = quality.data.items.reduce((n, s) => n + s.observations, 0);
  const { counts } = quality.data;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex flex-wrap items-center gap-2 text-sm text-fg-muted">
          <span className="tabular font-mono text-fg">{total.toLocaleString("en")}</span> observations in{" "}
          <span className="tabular font-mono text-fg">{quality.data.items.length}</span> native series ·
          <Badge tone="ok">{counts.pass ?? 0} pass</Badge>
          <Badge tone="warn">{counts.warn ?? 0} warn</Badge>
          <Badge tone="danger">{counts.fail ?? 0} failed</Badge>
          <Badge tone="neutral" dashed>
            {counts.not_synced ?? 0} not synced
          </Badge>
        </p>
        <Segmented label="Filter by source" options={[...SOURCES]} value={source} onChange={setSource} />
      </div>
      <StoredSeriesTable items={items} showGeo />
      <p className="text-xs text-fg-subtle">
        Report generated {formatDateTimeUtc(quality.data.generated_at)}. Checks come from the most recent sync attempt of each
        series; a failed attempt is shown even when older observations remain stored. CSV downloads contain the raw stored
        rows with per-row source URL, retrieval time and attribution.
      </p>
    </div>
  );
}
