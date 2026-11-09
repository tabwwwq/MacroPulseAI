"use client";

import { CircleCheck, CircleDashed, Construction } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { getModule } from "@/lib/modules";
import { useSourcesStatus } from "@/lib/queries";

/**
 * Honest page for a module that is not built yet: what it will do, when, and which prerequisites
 * are met right now (checked live where the API can tell). It never renders simulated output.
 */
export function ModulePlaceholder({ moduleId }: { moduleId: string }) {
  const mod = getModule(moduleId);
  const sources = useSourcesStatus();
  const dataSynced = (sources.data?.items.filter((s) => s.last_success_at).length ?? 0) > 0;

  function prerequisiteMet(p: string): boolean {
    if (p.startsWith("Observations ingested")) return dataSynced;
    return false; // models, backtests and snapshots do not exist yet
  }

  return (
    <>
      <PageHeader
        eyebrow={mod.group}
        title={mod.label}
        description={mod.summary}
        meta={
          <Badge tone="neutral" dashed>
            Scheduled · Phase {mod.phase}
          </Badge>
        }
      />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title={
              <span className="inline-flex items-center gap-2">
                <Construction className="size-4 text-warn" aria-hidden />
                Not built yet
              </span>
            }
            description="This page intentionally shows no numbers or charts until the underlying data and models are real."
          />
          <CardBody>
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-fg-subtle">Planned capabilities</p>
            <ul className="space-y-2.5">
              {mod.capabilities.map((c) => (
                <li key={c} className="flex gap-3 text-sm text-fg-muted">
                  <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-accent/70" />
                  {c}
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Prerequisites" description="Checked against the live API where possible." />
          <CardBody>
            <ul className="space-y-3">
              {mod.prerequisites.map((p) => {
                const met = prerequisiteMet(p);
                const Icon = met ? CircleCheck : CircleDashed;
                return (
                  <li key={p} className="flex items-start gap-3 text-sm">
                    <Icon className={met ? "mt-0.5 size-4 text-ok" : "mt-0.5 size-4 text-fg-subtle"} aria-hidden />
                    <span className={met ? "text-fg" : "text-fg-muted"}>
                      {p}
                      <span className="sr-only">{met ? " — met" : " — not met yet"}</span>
                    </span>
                  </li>
                );
              })}
            </ul>
          </CardBody>
        </Card>
      </div>
    </>
  );
}
