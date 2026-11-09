import type { Metadata } from "next";

import { CoverageMatrix } from "@/components/data/coverage-matrix";
import { SeriesInventory } from "@/components/data/series-inventory";
import { SourceRegistry } from "@/components/data/source-registry";
import { SystemStatus } from "@/components/data/system-status";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Data observatory" };

export default function DataObservatoryPage() {
  return (
    <>
      <PageHeader
        eyebrow="Platform"
        title="Data observatory"
        description="Verify that every number comes from a sourced record: source health, freshness, coverage, lineage and the raw stored rows."
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
          <CardHeader
            title="Stored series & lineage"
            description="Each native official series: exact request, rows stored, span, last fetch and the latest quality checks. Download the raw rows to verify any number shown in the app."
          />
          <CardBody>
            <WidgetBoundary label="Series inventory">
              <SeriesInventory />
            </WidgetBoundary>
          </CardBody>
        </Card>
        <Card className="xl:col-span-3">
          <CardHeader
            title="Coverage matrix"
            description="Country × indicator availability from the live probe of the official APIs (see docs/DATA_FEASIBILITY.md). Click a cell for the country's source table."
          />
          <CardBody>
            <CoverageMatrix />
          </CardBody>
        </Card>
      </div>
    </>
  );
}
