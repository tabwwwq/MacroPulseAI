"use client";

import * as Tabs from "@radix-ui/react-tabs";
import { ExternalLink, Landmark } from "lucide-react";
import Link from "next/link";

import type { CatalogEntry, Country } from "@macropulse/shared-types";

import { IndicatorChart } from "@/components/data/indicator-chart";
import { KpiGrid } from "@/components/data/kpi-grid";
import { RangeControl, useRange } from "@/components/data/range-control";
import { RevisionsCard } from "@/components/data/revisions-card";
import { StoredSeriesTable } from "@/components/data/stored-series-table";
import { SupportBadge } from "@/components/data/support-badge";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { availabilityReason, MAPPING_STATUS, sourceLabel } from "@/lib/mapping";
import { useCatalog, useCountry, useDataQuality } from "@/lib/queries";
import type { RangeKey } from "@/lib/series";

const TABS = [
  { id: "overview", label: "Overview", categories: [] as string[] },
  { id: "growth", label: "Growth", categories: ["growth", "leading", "reference"] },
  { id: "prices", label: "Prices", categories: ["prices"] },
  { id: "labor", label: "Labor", categories: ["labor"] },
  { id: "monetary", label: "Monetary", categories: ["monetary"] },
  { id: "fiscal", label: "Fiscal", categories: ["fiscal"] },
  { id: "data", label: "Data", categories: [] as string[] },
] as const;
type TabId = (typeof TABS)[number]["id"];

/** Tab -> indicator whose ALFRED revision history is shown under the charts (US only). */
const REVISION_TAB: Partial<Record<TabId, string>> = {
  growth: "real_gdp_qoq",
  prices: "inflation_yoy",
  labor: "unemployment_rate",
};

function isTab(value: string | null): value is TabId {
  return TABS.some((t) => t.id === value);
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-surface-2/50 px-4 py-3">
      <dt className="text-xs text-fg-subtle">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-fg">{children}</dd>
    </div>
  );
}

function IndicatorPanel({ entry, iso2, asOf, range }: { entry: CatalogEntry; iso2: string; asOf: string | null; range: RangeKey }) {
  const status = MAPPING_STATUS[entry.mapping.status];
  const id = entry.indicator.id;
  return (
    <WidgetBoundary label={entry.indicator.name}>
      <IndicatorChart
        iso2={iso2}
        indicator={id}
        title={entry.indicator.name}
        asOf={asOf}
        range={range}
        reference={id === "real_gdp_qoq" || id === "real_gdp_yoy" || id === "unemployment_rate"}
        defaultKind={id === "real_gdp_qoq" ? "bar" : "line"}
        extra={
          <Badge tone={status.tone} dashed={status.tone === "neutral"} title={availabilityReason(entry)}>
            {status.label}
          </Badge>
        }
      />
    </WidgetBoundary>
  );
}

/** Stored native series behind this country: lineage, latest checks and the raw CSV. */
function LineageTable({ iso2 }: { iso2: string }) {
  const quality = useDataQuality(iso2);
  return (
    <Card className="mt-4">
      <CardHeader
        title="Stored series & lineage"
        description="Every native series the indicators above are derived from: exact request, rows stored, fetch time and the checks of the latest sync attempt."
      />
      <CardBody>
        {quality.isError ? (
          <ErrorState error={quality.error} onRetry={() => void quality.refetch()} />
        ) : quality.isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <StoredSeriesTable items={quality.data.items} />
        )}
      </CardBody>
    </Card>
  );
}

function DataTab({ entries }: { entries: CatalogEntry[] }) {
  return (
    <Card>
      <CardHeader
        title="Source mapping"
        description="Verified by a live probe of the official APIs. Probe metadata describes what the source publishes; the Stored column counts rows actually in the database."
      />
      <CardBody>
        <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
          <table className="w-full min-w-[860px] text-left text-sm">
            <caption className="sr-only">Indicator sources and ingestion state</caption>
            <thead>
              <tr className="border-b border-line text-xs text-fg-subtle">
                <th scope="col" className="py-2 pr-4 font-medium">Indicator</th>
                <th scope="col" className="py-2 pr-4 font-medium">Source · dataset</th>
                <th scope="col" className="py-2 pr-4 font-medium">Series key / filter</th>
                <th scope="col" className="py-2 pr-4 font-medium">Probe status</th>
                <th scope="col" className="py-2 pr-4 font-medium">Latest in probe</th>
                <th scope="col" className="py-2 font-medium">Stored</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => {
                const status = MAPPING_STATUS[e.mapping.status];
                return (
                  <tr key={e.indicator.id} className="border-b border-line/60 align-top last:border-0">
                    <th scope="row" className="py-3 pr-4 font-medium text-fg">
                      {e.indicator.name}
                      <p className="text-xs font-normal text-fg-subtle">{e.indicator.unit}</p>
                    </th>
                    <td className="py-3 pr-4 text-fg-muted">
                      {e.mapping.docs_url ? (
                        <a href={e.mapping.docs_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 hover:text-accent">
                          {sourceLabel(e)}
                          <ExternalLink className="size-3" aria-hidden />
                          <span className="sr-only">(opens in a new tab)</span>
                        </a>
                      ) : (
                        <span className="text-fg-subtle">—</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs text-fg-muted">{e.mapping.series_key ?? "—"}</td>
                    <td className="py-3 pr-4">
                      <Badge tone={status.tone} dashed={status.tone === "neutral"} title={availabilityReason(e)}>
                        {status.label}
                      </Badge>
                    </td>
                    <td className="tabular py-3 pr-4 font-mono text-xs text-fg-muted">{e.mapping.probe_last_period ?? "—"}</td>
                    <td className="tabular py-3 font-mono text-xs text-fg">{e.ingestion.observations}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardBody>
    </Card>
  );
}

function OverviewTab({ country, asOf }: { country: Country; asOf: string | null }) {
  const sharedRate = country.policy_rate_scope === "euro_area_shared";
  return (
    <div className="space-y-4">
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Fact label="ISO codes">
          <span className="font-mono">
            {country.iso2} · {country.iso3}
          </span>
        </Fact>
        <Fact label="Currency">{country.currency}</Fact>
        <Fact label="Euro area member">{country.euro_area_member ? "Yes" : "No"}</Fact>
        <Fact label="Policy rate scope">{sharedRate ? "Shared euro area (ECB)" : "National"}</Fact>
      </dl>
      <KpiGrid iso2={country.iso2} asOf={asOf} />
      <Card>
        <CardHeader
          title={
            <span className="inline-flex items-center gap-2">
              <Landmark className="size-4 text-fg-subtle" aria-hidden />
              Monetary policy note
            </span>
          }
        />
        <CardBody className="text-sm leading-relaxed text-fg-muted">
          {sharedRate ? (
            <p>
              {country.name} is a euro area member. Its policy rate is the ECB&apos;s shared rate (deposit facility
              / main refinancing), not a national central-bank rate, and is labelled as shared everywhere.
            </p>
          ) : (
            <p>
              {country.name} sets a national policy rate. NBER recession dates (FRED <span className="font-mono">USREC</span>)
              are shown only as an external reference — never as the GDP-based technical-recession target.
            </p>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

export function CountryView({ iso2 }: { iso2: string }) {
  const { asOf, params, setParam } = useAppContext();
  const country = useCountry(iso2);
  const catalog = useCatalog(iso2);
  const tabParam = params.get("tab");
  const tab: TabId = isTab(tabParam) ? tabParam : "overview";
  const [range] = useRange();

  if (country.isPending) {
    return (
      <div aria-busy="true" aria-label="Loading country">
        <Skeleton className="mb-3 h-4 w-24" />
        <Skeleton className="mb-8 h-9 w-72" />
        <Skeleton className="h-10 w-full max-w-xl rounded-lg" />
      </div>
    );
  }

  if (country.isError) {
    const error = country.error;
    if (error instanceof ApiError && error.code === "unsupported_country") {
      return (
        <EmptyState
          title={`“${iso2.toUpperCase()}” is not a supported country`}
          action={
            <Link href="/countries" className={buttonVariants({ size: "sm" })}>
              See supported countries
            </Link>
          }
        >
          {error.message}
        </EmptyState>
      );
    }
    return <ErrorState error={error} onRetry={() => void country.refetch()} />;
  }

  const data = country.data;
  const entries = catalog.data?.countries[0]?.items ?? [];

  return (
    <>
      <PageHeader
        eyebrow={`Country profile · ${data.iso2} / ${data.iso3}`}
        title={data.name}
        description={`${data.region} · ${data.currency} · primary real-GDP source: ${data.primary_gdp_source}`}
        meta={
          <>
            <Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>
            <SupportBadge support={data.support} />
          </>
        }
      />

      <Tabs.Root value={tab} onValueChange={(v) => setParam("tab", v === "overview" ? null : v)}>
        <Tabs.List
          aria-label="Country sections"
          className="relative mb-5 flex gap-1 overflow-x-auto border-b border-line [scrollbar-width:none]"
        >
          {TABS.map((t) => (
            <Tabs.Trigger
              key={t.id}
              value={t.id}
              className="-mb-px shrink-0 border-b-2 border-transparent px-3 py-2.5 text-sm text-fg-muted transition-colors hover:text-fg data-[state=active]:border-accent data-[state=active]:text-fg"
            >
              {t.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <Tabs.Content value="overview" className="focus:outline-none">
          <OverviewTab country={data} asOf={asOf} />
        </Tabs.Content>

        {TABS.filter((t) => t.categories.length > 0).map((t) => {
          const inTab = entries.filter((e) => (t.categories as readonly string[]).includes(e.indicator.category));
          return (
            <Tabs.Content key={t.id} value={t.id} className="focus:outline-none">
              {catalog.isError ? (
                <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} />
              ) : catalog.isPending ? (
                <Skeleton className="h-72 w-full rounded-card" />
              ) : (
                <>
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-xs text-fg-subtle">
                      Stored official observations{asOf ? ` for periods up to ${asOf}` : ""}. Table view, CSV and PNG on
                      each chart; the source link opens the exact request.
                    </p>
                    <RangeControl />
                  </div>
                  <div className="grid gap-4 lg:grid-cols-2">
                    {inTab.map((e) => (
                      <IndicatorPanel key={e.indicator.id} entry={e} iso2={data.iso2} asOf={asOf} range={range} />
                    ))}
                  </div>
                  {REVISION_TAB[t.id] && data.iso2 === "US" ? (
                    <div className="mt-4">
                      <RevisionsCard iso2={data.iso2} indicator={REVISION_TAB[t.id] ?? ""} range={range} />
                    </div>
                  ) : null}
                </>
              )}
            </Tabs.Content>
          );
        })}

        <Tabs.Content value="data" className="focus:outline-none">
          {catalog.isError ? (
            <ErrorState error={catalog.error} onRetry={() => void catalog.refetch()} />
          ) : catalog.isPending ? (
            <Skeleton className="h-72 w-full rounded-card" />
          ) : (
            <>
              <DataTab entries={entries} />
              <LineageTable iso2={data.iso2} />
            </>
          )}
        </Tabs.Content>
      </Tabs.Root>
    </>
  );
}
