import type { Metadata } from "next";

import { SourceRegistry } from "@/components/data/source-registry";
import { SystemStatus } from "@/components/data/system-status";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/states";

export const metadata: Metadata = { title: "Data observatory" };

export default function DataObservatoryPage() {
  return (
    <>
      <PageHeader
        eyebrow="Platform"
        title="Data observatory"
        description="Verify that every number comes from a sourced record: source health, freshness, coverage and lineage."
        meta={
          <Badge tone="accent" dashed>
            Foundation · coverage & lineage in Phase 4
          </Badge>
        }
      />
      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Source health"
            description="Derived from recorded ingestion runs only. API keys are server-side; only their presence is shown."
          />
          <CardBody>
            <SourceRegistry />
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Platform status" />
          <CardBody>
            <SystemStatus />
          </CardBody>
        </Card>
        <Card className="xl:col-span-3">
          <CardHeader title="Coverage heatmap" description="Country × indicator availability with staleness markers." />
          <CardBody>
            <EmptyState title="No observations stored yet">
              The coverage matrix is computed from stored observations, so it stays empty until the first data
              sync (Phase 3). Pre-ingestion feasibility evidence is documented in docs/DATA_FEASIBILITY.md.
            </EmptyState>
          </CardBody>
        </Card>
      </div>
    </>
  );
}
