"use client";

import * as Select from "@radix-ui/react-select";
import { ChartLine, Check, ChevronDown } from "lucide-react";
import { useRef, useState } from "react";

import type { ForecastModel, ForecastResponse } from "@macropulse/shared-types";

import { ChartFrame } from "@/components/charts/chart-frame";
import { ForecastChart, type ForecastChartHandle } from "@/components/charts/forecast-chart";
import { ProvenanceDetails } from "@/components/data/provenance";
import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { Fact, Warning } from "@/components/ui/facts";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState, Notice } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { formatAsOf } from "@/lib/as-of";
import { cn } from "@/lib/cn";
import { useAppContext } from "@/lib/context";
import { downloadDataUrl, downloadText } from "@/lib/export";
import {
  backtestSeries,
  coverageStatus,
  FORECAST_HORIZONS,
  FORECAST_METRICS,
  forecastToCsv,
  horizonLabel,
  metricGroups,
  parseHorizon,
  parseMetric,
  pickModel,
  stepUnit,
} from "@/lib/forecast";
import { formatDateTimeUtc } from "@/lib/format";
import { useCountries, useForecast } from "@/lib/queries";

const MODEL_OPTIONS = [
  { value: "ar", label: "Ridge AR" },
  { value: "mean", label: "Rolling mean" },
  { value: "naive", label: "Naive" },
];

const num = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const pct = new Intl.NumberFormat("en-GB", { style: "percent", maximumFractionDigits: 0 });

function n2(v: number | null | undefined): string {
  return typeof v === "number" && Number.isFinite(v) ? num.format(v) : "N/A";
}

function HorizonSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle" id="horizon-label">
        Horizon
      </p>
      <Select.Root value={value} onValueChange={onChange}>
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
              {FORECAST_HORIZONS.map((h) => (
                <Select.Item
                  key={h}
                  value={h}
                  className="relative flex cursor-pointer select-none items-center rounded-lg py-1.5 pl-2.5 pr-8 text-sm text-fg outline-none data-[highlighted]:bg-surface-2"
                >
                  <Select.ItemText>{horizonLabel(Number(h))}</Select.ItemText>
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
  );
}

function ForecastCard({ fc, model, countryName }: { fc: ForecastResponse; model: ForecastModel; countryName: string }) {
  const chart = useRef<ForecastChartHandle>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const fileBase = `macropulse-${fc.country.toLowerCase()}-${fc.metric}-${model.key}-h${fc.horizon_quarters}${fc.as_of ? `-asof-${fc.as_of}` : ""}`;

  function exportFile(format: "csv" | "png") {
    try {
      if (format === "csv") downloadText(`${fileBase}.csv`, forecastToCsv(fc, model));
      else {
        const url = chart.current?.getPngDataUrl();
        if (!url) throw new Error("Chart image unavailable");
        downloadDataUrl(`${fileBase}.png`, url);
      }
      setExportError(null);
    } catch {
      setExportError(`${format.toUpperCase()} export failed. Please try again.`);
    }
  }

  return (
    <Card aria-label="Forecast chart">
      <CardHeader
        title={`${fc.indicator_name} · ${countryName}`}
        description={`Published values solid; ${model.name} forecast dashed with its empirical 80 % interval. Next ${stepUnit(fc.frequency, fc.steps)} from ${fc.origin}.`}
        action={
          model.available ? (
            <div className="flex gap-2">
              <Button size="sm" onClick={() => exportFile("csv")}>CSV</Button>
              <Button size="sm" onClick={() => exportFile("png")}>PNG</Button>
            </div>
          ) : undefined
        }
      />
      <CardBody>
        {model.available ? (
          <ForecastChart
            ref={chart}
            actuals={fc.actuals}
            path={model.path}
            realised={fc.realised}
            origin={fc.origin}
            unit={fc.unit}
            modelName={model.name}
            ariaLabel={`${fc.indicator_name} for ${countryName}: published history and ${model.name} forecast`}
          />
        ) : (
          <EmptyState title={`${model.name} cannot forecast from this origin`}>{model.reason}</EmptyState>
        )}
        {exportError ? <p role="alert" className="mt-3 text-sm text-danger">{exportError}</p> : null}
        <p className="mt-3 text-xs leading-relaxed text-fg-subtle">{model.description}</p>
        <footer className="mt-3 border-t border-line pt-3 text-xs text-fg-subtle">
          Source: {fc.provenance.docs_url ? (
            <a className="text-accent underline underline-offset-2" href={fc.provenance.docs_url} target="_blank" rel="noopener noreferrer">
              {fc.provenance.source_name} · {fc.provenance.dataset}
            </a>
          ) : `${fc.provenance.source_name} · ${fc.provenance.dataset}`}
          {` · retrieved ${formatDateTimeUtc(fc.provenance.retrieved_at)} · ${fc.transform}`}
        </footer>
      </CardBody>
    </Card>
  );
}

function ProjectionCard({ fc, model }: { fc: ForecastResponse; model: ForecastModel }) {
  const realised = new Map(fc.realised.map((r) => [r.period, r.value]));
  const withheld = model.path.some((p) => p.lower === null);
  const metric = fc.backtest.metrics.find((m) => m.model === model.key && m.step === fc.steps);
  const under = coverageStatus(metric?.coverage, fc.nominal_coverage) === "under";
  return (
    <Card>
      <CardHeader title="Projection" description={`${model.name} · unit ${fc.unit}`} action={<Badge tone="accent">Model forecast</Badge>} />
      <CardBody className="space-y-4">
        {model.path.length ? (
          <div className="relative -mx-5 max-h-72 overflow-auto px-5">
            <table className="w-full text-left text-xs tabular">
              <caption className="sr-only">Forecast path with empirical 80 % intervals</caption>
              <thead className="sticky top-0 bg-surface text-fg-subtle">
                <tr>
                  <th scope="col" className="py-1.5 font-medium">Period</th>
                  <th scope="col" className="py-1.5 text-right font-medium">Forecast</th>
                  <th scope="col" className="py-1.5 text-right font-medium">80 % interval</th>
                  {fc.realised.length ? <th scope="col" className="py-1.5 text-right font-medium">Published</th> : null}
                </tr>
              </thead>
              <tbody className="font-mono text-fg">
                {model.path.map((p) => (
                  <tr key={p.period} className="border-t border-line/60">
                    <th scope="row" className="py-1.5 font-normal text-fg-muted">{p.period}</th>
                    <td className="py-1.5 text-right">{n2(p.value)}</td>
                    <td className="py-1.5 text-right text-fg-muted">{p.lower === null ? "N/A" : `${n2(p.lower)} to ${n2(p.upper)}`}</td>
                    {fc.realised.length ? <td className="py-1.5 text-right text-ok">{n2(realised.get(p.period))}</td> : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-fg-muted">No forecast path from this model.</p>
        )}
        {withheld ? (
          <Warning>
            Interval withheld where fewer than {fc.min_errors} past forecast errors exist for that step: there is no empirical basis for it.
          </Warning>
        ) : null}
        {under ? (
          <Warning>
            In the backtest this model&apos;s 80 % interval at {stepUnit(fc.frequency, fc.steps)} contained only{" "}
            <span className="font-mono text-fg">{pct.format(metric?.coverage ?? 0)}</span> of later-published values. Read it as too narrow.
          </Warning>
        ) : null}
        <dl>
          <Fact label="Forecast origin">{fc.origin}</Fact>
          <Fact label="Information cut-off">{fc.cutoff}</Fact>
          <Fact label="Backtest origins">
            {fc.backtest.first_origin ?? "—"} to {fc.backtest.last_origin ?? "—"}
          </Fact>
          <Fact label="Version">{fc.version}</Fact>
          <Fact label="Computed">{formatDateTimeUtc(fc.generated_at)}</Fact>
        </dl>
      </CardBody>
    </Card>
  );
}

function DiagnosticsCard({ fc, selected }: { fc: ForecastResponse; selected: string }) {
  const groups = metricGroups(fc.backtest.metrics);
  const names = new Map(fc.models.map((m) => [m.key, m.name]));
  return (
    <Card>
      <CardHeader
        title="Backtest diagnostics"
        description={`Rolling-origin backtest, every origin ${fc.backtest.first_origin ?? "—"} to ${fc.backtest.last_origin ?? "—"}. Errors are later-published minus forecast; coverage uses intervals built only from errors known at each origin.`}
      />
      <CardBody>
        <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
          <table className="w-full min-w-[720px] text-left text-xs tabular">
            <caption className="sr-only">Forecast accuracy and interval coverage by horizon and model</caption>
            <thead className="text-fg-subtle">
              <tr>
                <th scope="col" className="py-2 font-medium">Horizon</th>
                <th scope="col" className="py-2 font-medium">Model</th>
                <th scope="col" className="py-2 text-right font-medium">Forecasts</th>
                <th scope="col" className="py-2 text-right font-medium">MAE</th>
                <th scope="col" className="py-2 text-right font-medium">RMSE</th>
                <th scope="col" className="py-2 text-right font-medium">RMSE vs naive</th>
                <th scope="col" className="py-2 text-right font-medium">Bias</th>
                <th scope="col" className="py-2 text-right font-medium">80 % coverage</th>
                <th scope="col" className="py-2 text-right font-medium">Mean width</th>
              </tr>
            </thead>
            <tbody className="font-mono text-fg">
              {groups.flatMap(({ horizon, rows, best }) =>
                rows.map((m, i) => {
                  const status = coverageStatus(m.coverage, fc.nominal_coverage);
                  const isSelected = m.model === selected && m.step === fc.steps;
                  return (
                    <tr
                      key={`${horizon}-${m.model}`}
                      aria-current={isSelected ? "true" : undefined}
                      className={cn("border-t border-line/60", i === 0 && "border-line", isSelected && "bg-accent/[0.07]")}
                    >
                      <td className="py-1.5 font-sans text-fg-muted">{i === 0 ? horizonLabel(horizon, fc.frequency) : ""}</td>
                      <th scope="row" className="py-1.5 font-sans font-normal">
                        {names.get(m.model) ?? m.model}
                        {best === m.model ? <span className="ml-2 text-[11px] text-fg-subtle">lowest RMSE</span> : null}
                      </th>
                      <td className="py-1.5 text-right text-fg-muted">{m.n}</td>
                      <td className="py-1.5 text-right">{n2(m.mae)}</td>
                      <td className="py-1.5 text-right">{n2(m.rmse)}</td>
                      <td className="py-1.5 text-right">
                        {m.model === "naive" ? (
                          <span className="text-fg-subtle">reference</span>
                        ) : m.rel_rmse === null ? (
                          "N/A"
                        ) : (
                          <>
                            {n2(m.rel_rmse)}{" "}
                            <span className={cn("font-sans text-[11px]", m.rel_rmse < 1 ? "text-ok" : "text-warn")}>
                              {m.rel_rmse < 1 ? "better" : "worse"}
                            </span>
                          </>
                        )}
                      </td>
                      <td className="py-1.5 text-right text-fg-muted">{n2(m.bias)}</td>
                      <td className="py-1.5 text-right">
                        {status === "na" ? (
                          <span title={m.note ?? undefined}>N/A</span>
                        ) : (
                          <>
                            {pct.format(m.coverage ?? 0)}
                            <span className="text-fg-subtle"> ({m.coverage_n})</span>
                            {status === "under" ? (
                              <Badge tone="warn" className="ml-2 font-sans">under</Badge>
                            ) : null}
                          </>
                        )}
                      </td>
                      <td className="py-1.5 text-right text-fg-muted">{n2(m.mean_width)}</td>
                    </tr>
                  );
                }),
              )}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-fg-subtle">
          RMSE vs naive below 1 means smaller errors than the last-value forecast on the same origins. Coverage is the share of
          later-published values inside the 80 % interval (count in brackets); “under” marks coverage more than 10 points below
          80 %. “Lowest RMSE” is chosen on this same backtest, so it is optimistic for that model. Unit: {fc.unit}.
        </p>
      </CardBody>
    </Card>
  );
}

function ForecastBody({ iso2, countryName }: { iso2: string; countryName: string }) {
  const { asOf, params, setParam } = useAppContext();
  const metric = parseMetric(params.get("metric"));
  const horizon = parseHorizon(params.get("horizon"));
  const fc = useForecast(iso2, metric, Number(horizon), asOf);
  const model = fc.data ? pickModel(fc.data.models, params.get("model")) : undefined;
  const answer = fc.error instanceof ApiError && [404, 422, 503].includes(fc.error.status) ? fc.error : null;

  return (
    <>
      <Card className="mb-4">
        <CardBody className="flex flex-col gap-4 pt-5 lg:flex-row lg:flex-wrap lg:items-end lg:justify-between">
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Indicator</p>
            <Segmented label="Forecast indicator" options={[...FORECAST_METRICS]} value={metric} onChange={(v) => setParam("metric", v)} />
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Model</p>
            <Segmented label="Forecast model" options={MODEL_OPTIONS} value={model?.key ?? "ar"} onChange={(v) => setParam("model", v)} />
          </div>
          <HorizonSelect value={horizon} onChange={(v) => setParam("horizon", v)} />
        </CardBody>
      </Card>

      {asOf ? (
        <Notice className="mb-4">
          Forecast made with what had been published by the end of {asOf} (conservative publication lags on today&apos;s revised data,
          not the original vintages). Values published later are drawn in green for comparison.
        </Notice>
      ) : null}

      {fc.isPending ? (
        <div className="grid gap-4 xl:grid-cols-3" role="status" aria-label="Loading forecast">
          <Skeleton className="h-[440px] rounded-card xl:col-span-2" />
          <Skeleton className="h-[440px] rounded-card" />
        </div>
      ) : answer ? (
        <EmptyState icon={<ChartLine className="size-6" aria-hidden />} title="No forecast for this selection">
          {answer.message}
        </EmptyState>
      ) : fc.error || !fc.data || !model ? (
        <ErrorState error={fc.error} onRetry={() => void fc.refetch()} />
      ) : (
        <div className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="min-w-0 xl:col-span-2">
              <WidgetBoundary label="Forecast chart">
                <ForecastCard fc={fc.data} model={model} countryName={countryName} />
              </WidgetBoundary>
            </div>
            <ProjectionCard fc={fc.data} model={model} />
          </div>
          <DiagnosticsCard fc={fc.data} selected={model.key} />
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="min-w-0 xl:col-span-2">
              <WidgetBoundary label="Backtest chart">
                <ChartFrame
                  title={`Backtest · ${model.name} at ${stepUnit(fc.data.frequency, fc.data.steps)}`}
                  description="Each forecast is placed at the period it was aiming for, next to the value published later."
                  series={backtestSeries(fc.data, model)}
                  emptyTitle="No scored backtest forecasts"
                  emptyMessage="Not enough history before the origin to score this model at this horizon."
                  exportName={`macropulse-${iso2.toLowerCase()}-${fc.data.metric}-${model.key}-backtest-${fc.data.steps}`}
                  height={280}
                />
              </WidgetBoundary>
            </div>
            <Card>
              <CardHeader title="Method and assumptions" description="What these forecasts are, and are not." />
              <CardBody className="space-y-4 text-xs leading-relaxed text-fg-muted">
                <ul className="list-disc space-y-1.5 pl-4">
                  {fc.data.assumptions.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
                <ProvenanceDetails provenance={fc.data.provenance} transform={fc.data.transform} />
              </CardBody>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}

export function ForecastsView() {
  const { country, asOf } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);

  return (
    <>
      <PageHeader
        eyebrow="Models"
        title="Forecast studio"
        description="Multi-step forecasts of GDP growth, inflation and unemployment with empirical intervals, always scored against a naive baseline in rolling-origin backtests."
        meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
      />
      {!selected ? (
        <CountryRequired purpose="Forecasts are per country and indicator." />
      ) : (
        <ForecastBody key={selected.iso2} iso2={selected.iso2} countryName={selected.name} />
      )}
    </>
  );
}
