"use client";

import { CircleCheck, CircleX } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/states";
import { useHealth, useReady, useSourcesStatus } from "@/lib/queries";

function Row({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  const Icon = ok ? CircleCheck : CircleX;
  return (
    <li className="flex items-start gap-3 py-2.5">
      <Icon className={ok ? "mt-0.5 size-4 shrink-0 text-ok" : "mt-0.5 size-4 shrink-0 text-warn"} aria-hidden />
      <div className="min-w-0">
        <p className="text-sm text-fg">
          {label} <span className="sr-only">{ok ? "OK" : "needs attention"}</span>
        </p>
        <p className="break-words font-mono text-xs text-fg-subtle">{detail}</p>
      </div>
    </li>
  );
}

/** Live platform checklist: API, database/schema/registry, sources and models. */
export function SystemStatus() {
  const health = useHealth();
  const ready = useReady();
  const sources = useSourcesStatus();

  if (ready.isPending || health.isPending) {
    return (
      <div className="space-y-3" aria-busy="true" aria-label="Loading platform status">
        {Array.from({ length: 5 }, (_, i) => (
          <Skeleton key={i} className="h-9" />
        ))}
      </div>
    );
  }
  if (ready.isError) {
    return <ErrorState error={ready.error} onRetry={() => void ready.refetch()} />;
  }

  const synced = sources.data?.items.filter((s) => s.last_success_at).length ?? 0;
  const total = sources.data?.items.length ?? 5;

  return (
    <div>
      <div className="mb-1 flex items-center gap-2">
        <Badge tone={ready.data.status === "ready" ? "ok" : "warn"}>
          {ready.data.status === "ready" ? "Ready" : "Not ready"}
        </Badge>
        {health.data ? (
          <span className="font-mono text-xs text-fg-subtle">
            v{health.data.version} · {health.data.environment}
          </span>
        ) : null}
      </div>
      <ul className="divide-y divide-line/60">
        {ready.data.checks.map((c) => (
          <Row key={c.name} label={c.name[0]?.toUpperCase() + c.name.slice(1)} ok={c.ok} detail={c.detail} />
        ))}
        <Row
          label="Official data"
          ok={synced > 0}
          detail={`${synced}/${total} sources synced — connectors arrive in Phase 3`}
        />
        <Row label="Models" ok={false} detail="No trained model artifacts — training pipeline arrives in Phase 5" />
      </ul>
    </div>
  );
}
