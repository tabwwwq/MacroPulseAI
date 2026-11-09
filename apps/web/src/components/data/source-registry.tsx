"use client";

import { ExternalLink, KeyRound } from "lucide-react";

import type { SourceStatus } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { formatDateTimeUtc } from "@/lib/format";
import { useSourcesStatus } from "@/lib/queries";

const STATUS: Record<SourceStatus["status"], { label: string; tone: "neutral" | "accent" | "ok" | "warn" | "danger" }> = {
  never_synced: { label: "Never synced", tone: "neutral" },
  running: { label: "Syncing", tone: "accent" },
  ok: { label: "OK", tone: "ok" },
  degraded: { label: "Degraded", tone: "warn" },
  failed: { label: "Failed", tone: "danger" },
};

function KeyCell({ source }: { source: SourceStatus }) {
  if (!source.requires_api_key) return <span className="text-fg-subtle">Not required</span>;
  return source.api_key_configured ? (
    <Badge tone="ok">
      <KeyRound className="size-3" aria-hidden />
      Configured
    </Badge>
  ) : (
    <Badge tone="warn">
      <KeyRound className="size-3" aria-hidden />
      Not configured
    </Badge>
  );
}

/** Official sources with health derived from recorded ingestion runs (no optimistic defaults). */
export function SourceRegistry({ compact = false }: { compact?: boolean }) {
  const { data, isPending, isError, error, refetch } = useSourcesStatus();

  if (isPending) {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Loading sources">
        {Array.from({ length: 5 }, (_, i) => (
          <Skeleton key={i} className="h-11" />
        ))}
      </div>
    );
  }
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />;

  return (
    <div className="relative -mx-5 overflow-x-auto px-5">
      <table className={`w-full text-left text-sm ${compact ? "min-w-[520px]" : "min-w-[760px]"}`}>
        <caption className="sr-only">Official data sources and their sync status</caption>
        <thead>
          <tr className="border-b border-line text-xs text-fg-subtle">
            <th scope="col" className="py-2 pr-4 font-medium">Source</th>
            <th scope="col" className="py-2 pr-4 font-medium">Status</th>
            <th scope="col" className="py-2 pr-4 font-medium">Last successful fetch</th>
            <th scope="col" className="py-2 pr-4 font-medium">API key</th>
            {!compact ? <th scope="col" className="py-2 font-medium">Attribution</th> : null}
          </tr>
        </thead>
        <tbody>
          {data.items.map((s) => {
            const status = STATUS[s.status];
            return (
              <tr key={s.id} className="border-b border-line/60 align-top last:border-0">
                <td className="py-3 pr-4">
                  <a
                    href={s.docs_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="inline-flex items-center gap-1.5 font-medium text-fg hover:text-accent"
                  >
                    {s.name}
                    <ExternalLink className="size-3 text-fg-subtle" aria-hidden />
                    <span className="sr-only">(documentation, opens in a new tab)</span>
                  </a>
                  <p className="text-xs text-fg-subtle">{s.publisher}</p>
                </td>
                <td className="py-3 pr-4">
                  <Badge tone={status.tone} dashed={s.status === "never_synced"}>
                    {status.label}
                  </Badge>
                  {s.last_error ? <p className="mt-1 max-w-56 text-xs text-danger">{s.last_error}</p> : null}
                </td>
                <td className="tabular py-3 pr-4 font-mono text-xs text-fg-muted">
                  {formatDateTimeUtc(s.last_success_at)}
                </td>
                <td className="py-3 pr-4">
                  <KeyCell source={s} />
                </td>
                {!compact ? <td className="py-3 text-xs text-fg-muted">{s.attribution}</td> : null}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
