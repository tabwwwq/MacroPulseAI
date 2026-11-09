import Link from "next/link";

import { CountryGrid } from "@/components/data/country-grid";
import { ModuleRoadmap } from "@/components/data/module-roadmap";
import { SourceRegistry } from "@/components/data/source-registry";
import { SystemStatus } from "@/components/data/system-status";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Notice } from "@/components/ui/states";

export default function OverviewPage() {
  return (
    <>
      <PageHeader
        eyebrow="Monitor"
        title="Macro overview"
        description="Economic health and technical-recession early warning for Belgium, Germany, France, the Netherlands and the United States — built only on official statistics."
        meta={
          <Badge tone="accent" dashed>
            Foundation build · Phase 1
          </Badge>
        }
      />

      <Notice className="mb-6">
        <p>
          <span className="font-medium text-fg">No economic observations have been ingested yet.</span> KPI tiles,
          risk timelines and release calendars appear once official data is synced (connectors: Phase 3,
          dashboards: Phase 4). Nothing on this page is sample or simulated data — everything below is live
          platform state from the API.
        </p>
      </Notice>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Choose a country"
            description="Support level is computed from data actually stored, so it reads “No data yet” until the first sync."
          />
          <CardBody>
            <CountryGrid />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Platform status" description="Live readiness checks." />
          <CardBody>
            <SystemStatus />
          </CardBody>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader
            title="Official sources"
            description="Freshness = last successful fetch (not the observation period or publication date)."
            action={
              <Link href="/data" className="text-xs font-medium text-accent hover:underline">
                Data observatory →
              </Link>
            }
          />
          <CardBody>
            <SourceRegistry compact />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Module roadmap" description="What is built, and when the rest lands." />
          <CardBody className="pt-2">
            <ModuleRoadmap />
          </CardBody>
        </Card>
      </div>
    </>
  );
}
