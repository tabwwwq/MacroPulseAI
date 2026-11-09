"use client";

import Link from "next/link";

import type { CatalogEntry, MappingStatus } from "@macropulse/shared-types";

import { ChartFrame } from "@/components/charts/chart-frame";
import { CountryGrid } from "@/components/data/country-grid";
import { KpiGrid } from "@/components/data/kpi-grid";
import { ModuleRoadmap } from "@/components/data/module-roadmap";
import { SourceRegistry } from "@/components/data/source-registry";
import { SystemStatus } from "@/components/data/system-status";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Notice } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { useCatalog, useCountries } from "@/lib/queries";

const STATUS_ORDER: MappingStatus[] = ["verified", "partial", "stale", "not_published", "unmapped"];

function entryFor(entries: CatalogEntry[], id: string): CatalogEntry | undefined {
  return entries.find((e) => e.indicator.id === id);
}

function IndicatorChart({ entry, iso2, title }: { entry: CatalogEntry | undefined; iso2: string; title: string }) {
  return (
    <ChartFrame
      title={title}
      description={entry ? `${entry.indicator.unit} · ${entry.mapping.native_frequency ?? entry.indicator.frequency}` : undefined}
      series={[]}
      emptyMessage={entry ? availabilityReason(entry) : "Loading source information…"}
      source={
        entry && sourceLabel(entry)
          ? { label: sourceLabel(entry) as string, href: entry.mapping.docs_url ?? undefined }
          : undefined
      }
      allowKindToggle
      exportName={`macropulse-${iso2.toLowerCase()}-${entry?.indicator.id ?? "indicator"}`}
      height={200}
    />
  );
}

function CountryDashboard({ iso2, asOf }: { iso2: string; asOf: string | null }) {
  const { hrefWithContext } = useAppContext();
  const catalog = useCatalog(iso2);
  const entries = catalog.data?.countries[0]?.items ?? [];
  const counts = STATUS_ORDER.map((s) => ({ s, n: entries.filter((e) => e.mapping.status === s).length })).filter((c) => c.n > 0);

  return (
    <div className="space-y-4">
      <WidgetBoundary label="Headline indicators">
        <KpiGrid iso2={iso2} asOf={asOf} />
      </WidgetBoundary>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="min-w-0 xl:col-span-2">
          <WidgetBoundary label="Risk timeline">
            <ChartFrame
              title="Technical-recession risk · next 2 quarters"
              description="Calibrated model probability over time, with historic technical recessions shaded."
              series={[]}
              emptyTitle="No trained model yet"
              emptyMessage="The risk timeline appears once a model has been trained and evaluated with walk-forward backtests (Phase 5). No probability is ever shown without a measured model."
              exportName={`macropulse-${iso2.toLowerCase()}-risk`}
              height={260}
            />
          </WidgetBoundary>
        </div>
        <Card>
          <CardHeader
            title="Data coverage"
            description={`Source status for ${iso2} from the live feasibility probe of ${catalog.data?.probe_date ?? "…"}.`}
            action={
              <Link href={hrefWithContext("/data")} className="text-xs font-medium text-accent hover:underline">
                Details →
              </Link>
            }
          />
          <CardBody>
            <ul className="space-y-2">
              {counts.map(({ s, n }) => (
                <li key={s} className="flex items-center justify-between gap-3 text-sm">
                  <Badge tone={MAPPING_STATUS[s].tone} dashed={MAPPING_STATUS[s].tone === "neutral"}>
                    {MAPPING_STATUS[s].label}
                  </Badge>
                  <span className="tabular font-mono text-fg">{n}</span>
                </li>
              ))}
            </ul>
            <p className="mt-4 text-xs leading-relaxed text-fg-muted">
              Stored observations: <span className="font-mono text-fg">0</span>. Coverage reflects what the
              official sources publish; values are ingested from Phase 3.
            </p>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <WidgetBoundary label="Inflation chart">
          <IndicatorChart entry={entryFor(entries, "inflation_yoy")} iso2={iso2} title="Inflation (y/y)" />
        </WidgetBoundary>
        <WidgetBoundary label="Unemployment chart">
          <IndicatorChart entry={entryFor(entries, "unemployment_rate")} iso2={iso2} title="Unemployment rate" />
        </WidgetBoundary>
      </div>
    </div>
  );
}

export function OverviewView() {
  const { country, asOf, setCountry } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);

  return (
    <>
      <PageHeader
        eyebrow="Monitor"
        title={selected ? `${selected.name} · macro overview` : "Macro overview"}
        description="Economic health and technical-recession early warning for Belgium, Germany, France, the Netherlands and the United States — built only on official statistics."
        meta={
          <>
            <Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>
            <Badge tone="accent" dashed>
              Design system · Phase 2
            </Badge>
          </>
        }
      />

      <Notice className="mb-6">
        <p>
          <span className="font-medium text-fg">No economic observations have been ingested yet.</span> Every tile
          and chart below is wired to the API and shows why it is empty — values appear after the official-data
          connectors run (Phase 3). Nothing on this page is sample or simulated data.
        </p>
      </Notice>

      {selected ? (
        <CountryDashboard iso2={selected.iso2} asOf={asOf} />
      ) : (
        <Card>
          <CardHeader
            title="Choose a country to begin"
            description="The selection is kept in the URL and follows you to every module (risk, forecasts, compare…)."
          />
          <CardBody>
            <CountryGrid onSelect={setCountry} />
          </CardBody>
        </Card>
      )}

      <h2 className="mb-3 mt-10 font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-fg-subtle">Platform</h2>
      <div className="grid gap-4 xl:grid-cols-3">
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
          />
          <CardBody>
            <SourceRegistry compact />
          </CardBody>
        </Card>
        <Card className="xl:col-span-3">
          <CardHeader title="Module roadmap" description="What is built, and when the rest lands." />
          <CardBody className="pt-2">
            <ModuleRoadmap />
          </CardBody>
        </Card>
      </div>
    </>
  );
}
