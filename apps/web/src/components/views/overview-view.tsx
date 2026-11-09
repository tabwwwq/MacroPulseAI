"use client";

import { Gauge } from "lucide-react";
import Link from "next/link";

import type { MappingStatus, StoredSeries } from "@macropulse/shared-types";

import { CountryGrid } from "@/components/data/country-grid";
import { IndicatorChart } from "@/components/data/indicator-chart";
import { KpiGrid } from "@/components/data/kpi-grid";
import { ModuleRoadmap } from "@/components/data/module-roadmap";
import { RangeControl, useRange } from "@/components/data/range-control";
import { SourceRegistry } from "@/components/data/source-registry";
import { SystemStatus } from "@/components/data/system-status";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState, Notice } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { formatRelative } from "@/lib/format";
import { MAPPING_STATUS } from "@/lib/mapping";
import { modelState, modelSummaryText } from "@/lib/models";
import { useCatalog, useCountries, useDataQuality, useModels, useSourcesStatus } from "@/lib/queries";

const STATUS_ORDER: MappingStatus[] = ["verified", "partial", "stale", "not_published", "unmapped"];
const HEALTH_TONE = { pass: "ok", warn: "warn", fail: "danger", not_synced: "neutral" } as const;

function withParam(href: string, key: string, value: string): string {
  return `${href}${href.includes("?") ? "&" : "?"}${key}=${encodeURIComponent(value)}`;
}

function seriesName(s: StoredSeries): string {
  const names: Record<string, string> = {
    real_gdp_qoq: "Real GDP",
    inflation_yoy: "Inflation",
    unemployment_rate: "Unemployment",
    policy_rate: "Policy rate",
    gov_debt_gdp: "Government debt",
    yield_spread: "Yield spread",
    nber_recession: "NBER reference",
  };
  return names[s.indicators.find((i) => i in names) ?? ""] ?? s.indicators.join(", ");
}

/** The newest stored period per series behind the country — reference periods, not release dates. */
function LatestObservations({ iso2 }: { iso2: string }) {
  const { hrefWithContext } = useAppContext();
  const quality = useDataQuality(iso2);
  return (
    <Card>
      <CardHeader
        title="Latest stored periods"
        description="Newest reference period per official series and when it was fetched. Release dates are not published by these APIs."
        action={
          <Link href={withParam(hrefWithContext(`/countries/${iso2.toLowerCase()}`), "tab", "data")} className="text-xs font-medium text-accent hover:underline">
            Lineage →
          </Link>
        }
      />
      <CardBody>
        {quality.isError ? (
          <ErrorState error={quality.error} onRetry={() => void quality.refetch()} />
        ) : quality.isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <ul className="divide-y divide-line/60">
            {quality.data.items.map((s) => (
              <li key={s.series_id} className="flex items-center justify-between gap-3 py-2 text-sm">
                <div className="min-w-0">
                  <p className="truncate text-fg">{seriesName(s)}</p>
                  <p className="truncate font-mono text-[11px] text-fg-subtle">
                    {s.source_id === "fred" ? "FRED" : s.source_id === "ecb" ? "ECB" : "Eurostat"} · {s.dataset}
                    {s.retrieved_at ? ` · fetched ${formatRelative(s.retrieved_at)}` : ""}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="tabular font-mono text-xs text-fg">{s.last_period ?? "—"}</span>
                  <Badge tone={HEALTH_TONE[s.health]} dashed={s.health === "not_synced"}>
                    {s.health === "not_synced" ? "not synced" : s.health}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function CountryDashboard({ iso2, asOf }: { iso2: string; asOf: string | null }) {
  const { hrefWithContext } = useAppContext();
  const catalog = useCatalog(iso2);
  const [range] = useRange();
  const models = modelState(useModels().data);
  const entries = catalog.data?.countries[0]?.items ?? [];
  const counts = STATUS_ORDER.map((s) => ({ s, n: entries.filter((e) => e.mapping.status === s).length })).filter((c) => c.n > 0);
  const storedIndicators = entries.filter((e) => e.ingestion.observations > 0).length;

  return (
    <div className="space-y-4">
      <WidgetBoundary label="Headline indicators">
        <KpiGrid iso2={iso2} asOf={asOf} />
      </WidgetBoundary>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <p className="text-xs text-fg-subtle">
          Charts show stored official observations{asOf ? ` for periods up to ${asOf}` : ""}; hover for values and source.
        </p>
        <RangeControl />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="min-w-0 xl:col-span-2">
          <WidgetBoundary label="Real GDP growth">
            <IndicatorChart
              iso2={iso2}
              indicator="real_gdp_qoq"
              asOf={asOf}
              range={range}
              height={280}
              reference
              defaultKind="bar"
            />
          </WidgetBoundary>
        </div>
        <div className="flex min-w-0 flex-col gap-4">
          <Card>
            <CardHeader title="Technical-recession risk" />
            <CardBody>
              <EmptyState
                icon={<Gauge className="size-5" aria-hidden />}
                title={models.trained ? "Model trained — display in Phase 6" : "No trained model yet"}
              >
                {modelSummaryText(models)} No probability is shown here until it can be presented with its
                version, as-of date, explanation and measured track record.
              </EmptyState>
            </CardBody>
          </Card>
          <Card>
            <CardHeader
              title="Data coverage"
              description={`Source status for ${iso2} from the live probe of ${catalog.data?.probe_date ?? "…"}.`}
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
                Indicators with stored observations:{" "}
                <span className="tabular font-mono text-fg">
                  {storedIndicators}/{entries.length}
                </span>
                . Coverage reflects what the official sources publish.
              </p>
            </CardBody>
          </Card>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <WidgetBoundary label="Inflation chart">
          <IndicatorChart iso2={iso2} indicator="inflation_yoy" asOf={asOf} range={range} height={220} />
        </WidgetBoundary>
        <WidgetBoundary label="Unemployment chart">
          <IndicatorChart iso2={iso2} indicator="unemployment_rate" asOf={asOf} range={range} height={220} />
        </WidgetBoundary>
        <WidgetBoundary label="Latest stored periods">
          <LatestObservations iso2={iso2} />
        </WidgetBoundary>
      </div>
    </div>
  );
}

/** What the page can and cannot show right now, derived from recorded ingestion runs. */
function DataStateNotice() {
  const sources = useSourcesStatus();
  if (!sources.data) return null;
  const synced = sources.data.items.filter((s) => s.last_success_at);
  if (synced.length > 0) return null;
  return (
    <Notice className="mb-6">
      <p>
        <span className="font-medium text-fg">No economic observations have been ingested yet.</span> Every tile and
        chart below is wired to the API and shows why it is empty. Run{" "}
        <code className="font-mono">uv run macropulse data-sync</code> on the server to fetch the official series. Nothing
        on this page is sample or simulated data.
      </p>
    </Notice>
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
            {asOf ? (
              <Badge tone="warn" dashed title="Values for periods ending by the cut-off, taken from today's revised data — not the figures published at the time.">
                Revised data, not vintages
              </Badge>
            ) : null}
          </>
        }
      />

      <DataStateNotice />

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
