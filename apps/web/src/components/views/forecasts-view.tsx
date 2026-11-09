"use client";

import * as Select from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";

import { ChartFrame } from "@/components/charts/chart-frame";
import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { EmptyState } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { availabilityReason, sourceLabel } from "@/lib/mapping";
import { useCatalog, useCountries } from "@/lib/queries";

const METRICS = [
  { value: "real_gdp_qoq", label: "GDP growth" },
  { value: "inflation_yoy", label: "Inflation" },
  { value: "unemployment_rate", label: "Unemployment" },
] as const;
type Metric = (typeof METRICS)[number]["value"];
const HORIZONS = ["1", "2", "4", "8"] as const;

export function ForecastsView() {
  const { country, asOf, params, setParam } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);
  const catalog = useCatalog(selected?.iso2 ?? null);
  const metricParam = params.get("metric");
  const metric: Metric = METRICS.some((m) => m.value === metricParam) ? (metricParam as Metric) : "real_gdp_qoq";
  const horizonParam = params.get("horizon");
  const horizon = (HORIZONS as readonly string[]).includes(horizonParam ?? "") ? (horizonParam as string) : "4";
  const entry = selected ? catalog.data?.countries[0]?.items.find((i) => i.indicator.id === metric) : undefined;
  const label = METRICS.find((m) => m.value === metric)?.label ?? metric;

  return (
    <>
      <PageHeader
        eyebrow="Models"
        title="Forecast studio"
        description="Multi-step forecasts with empirically calibrated intervals, always compared against naive baselines in rolling backtests."
        meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
      />

      {!selected ? (
        <CountryRequired purpose="Forecasts are per country and indicator." />
      ) : (
        <>
          <Card className="mb-4">
            <CardBody className="flex flex-col gap-4 pt-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Indicator</p>
                <Segmented label="Forecast indicator" options={[...METRICS]} value={metric} onChange={(v) => setParam("metric", v)} />
              </div>
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle" id="horizon-label">
                  Horizon
                </p>
                <Select.Root value={horizon} onValueChange={(v) => setParam("horizon", v)}>
                  <Select.Trigger
                    aria-labelledby="horizon-label"
                    className="inline-flex h-8 items-center gap-2 rounded-lg border border-line-strong bg-surface-2 px-3 text-sm text-fg hover:bg-elevated"
                  >
                    <Select.Value />
                    <Select.Icon>
                      <ChevronDown className="size-4 text-fg-subtle" aria-hidden />
                    </Select.Icon>
                  </Select.Trigger>
                  <Select.Portal>
                    <Select.Content position="popper" sideOffset={6} className="z-50 rounded-xl border border-line-strong bg-elevated p-1 shadow-card">
                      <Select.Viewport>
                        {HORIZONS.map((h) => (
                          <Select.Item
                            key={h}
                            value={h}
                            className="relative flex cursor-pointer select-none items-center rounded-lg py-1.5 pl-2.5 pr-8 text-sm text-fg outline-none data-[highlighted]:bg-surface-2"
                          >
                            <Select.ItemText>{h === "1" ? "1 quarter" : `${h} quarters`}</Select.ItemText>
                            <Select.ItemIndicator className="absolute right-2.5">
                              <Check className="size-4 text-accent" aria-hidden />
                            </Select.ItemIndicator>
                          </Select.Item>
                        ))}
                      </Select.Viewport>
                    </Select.Content>
                  </Select.Portal>
                </Select.Root>
              </div>
            </CardBody>
          </Card>

          <div className="grid gap-4 xl:grid-cols-3">
            <div className="min-w-0 xl:col-span-2">
              <WidgetBoundary label="Forecast chart">
                <ChartFrame
                  title={`${label} · ${selected.name} · ${horizon}-quarter horizon`}
                  description="Actuals solid, projection dashed, empirical interval ribbon from backtest errors."
                  series={[]}
                  isLoading={catalog.isPending}
                  emptyTitle="No forecast model backtested yet"
                  emptyMessage={entry ? `Forecasts start in Phase 7 on top of ingested data. ${availabilityReason(entry)}` : "Forecasts start in Phase 7."}
                  source={entry && sourceLabel(entry) ? { label: sourceLabel(entry) as string, href: entry.mapping.docs_url ?? undefined } : undefined}
                  exportName={`macropulse-${selected.iso2.toLowerCase()}-${metric}-forecast-h${horizon}`}
                  height={300}
                />
              </WidgetBoundary>
            </div>
            <Card>
              <CardHeader title="Backtest diagnostics" description="Rolling-origin errors vs naive and seasonal-naive baselines." />
              <CardBody>
                <EmptyState title="No backtests run">
                  MAE, RMSE and interval coverage per horizon appear here once a forecast model has been evaluated — N/A
                  rather than invented values.
                </EmptyState>
              </CardBody>
            </Card>
          </div>
        </>
      )}
    </>
  );
}
