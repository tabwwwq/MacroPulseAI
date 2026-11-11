"use client";

import { Gauge } from "lucide-react";
import Link from "next/link";

import type { RecessionEstimate } from "@macropulse/shared-types";

import { ChartFrame } from "@/components/charts/chart-frame";
import { Contributions } from "@/components/model/contributions";
import { ProbabilityGauge } from "@/components/model/probability-gauge";
import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Fact, Warning } from "@/components/ui/facts";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { formatDateTimeUtc, formatRelative } from "@/lib/format";
import { useCountries, useRecessionEstimate, useRecessionHistory } from "@/lib/queries";
import {
  formatMetric,
  formatProbability,
  formatSigned,
  HORIZON_CONFLICT_NOTE,
  horizonConflict,
  recessionShading,
  timelineSeries,
} from "@/lib/risk";

type Horizon = 2 | 4;

function outcomeText(e: RecessionEstimate): string {
  if (e.outcome.status === "censored") return `not known yet (window ${e.outcome.window.join(", ")})`;
  if (e.outcome.status === "missing") return "unknown (GDP missing in the window)";
  return e.outcome.label === 1 ? "technical recession occurred" : "no technical recession";
}

function EstimateCard({ e, horizon, other }: { e: RecessionEstimate; horizon: Horizon; other?: RecessionEstimate }) {
  const heldoutFails = e.track_record.beats_baseline_heldout === false;
  const conflict =
    other && other.as_of === e.as_of
      ? horizon === 2
        ? horizonConflict(e.probability, other.probability)
        : horizonConflict(other.probability, e.probability)
      : false;
  return (
    <Card>
      <CardHeader
        title={`Probability · next ${horizon} quarters`}
        description={`As of ${e.as_of} (data published by ${e.cutoff})`}
        action={e.in_sample ? <Badge tone="warn">In-sample fit</Badge> : <Badge tone="accent">Model estimate</Badge>}
      />
      <CardBody className="space-y-4">
        <ProbabilityGauge probability={e.probability} band={e.band} bands={e.bands} baseRate={e.base_rate} />
        {e.in_sample ? (
          <Warning>
            The outcome of this as-of quarter was part of the model&apos;s training data, so this number is a fit, not a
            forecast. The walk-forward estimate made without that knowledge was{" "}
            <span className="font-mono text-fg">{formatProbability(e.walk_forward_probability)}</span>
            {e.walk_forward_split ? ` (${e.walk_forward_split} backtest)` : ""}. Realised: {outcomeText(e)}.
          </Warning>
        ) : null}
        {conflict && other ? (
          <Warning>
            {HORIZON_CONFLICT_NOTE} The {horizon === 2 ? 4 : 2}-quarter estimate is {formatProbability(other.probability)}.
          </Warning>
        ) : null}
        {heldoutFails ? (
          <Warning>
            Track record: on the held-out years (2015 onwards) this model did <strong className="text-fg">not</strong> beat
            the historical base rate. Read the number as an analytical estimate, not a reliable forecast.
          </Warning>
        ) : null}
        <dl>
          <Fact label="Model">{e.model.name}</Fact>
          <Fact label="Version">{e.model.id}</Fact>
          <Fact label="Trained">{formatDateTimeUtc(e.model.trained_at)}</Fact>
          <Fact label="Labels used through">as-of {e.model.training_last_as_of ?? "—"}</Fact>
          <Fact label="Training sample">
            {e.model.training_rows ?? "—"} quarters · {e.model.training_events ?? "—"} events
          </Fact>
          <Fact label="Estimated at">{formatDateTimeUtc(e.prediction_timestamp)}</Fact>
          <Fact label="Data freshness">{e.data_freshness ? `fetched ${formatRelative(e.data_freshness)}` : "—"}</Fact>
          <Fact label="Outcome">{outcomeText(e)}</Fact>
          {e.inputs_stale.length ? <Fact label="Stale inputs">{e.inputs_stale.join(", ")}</Fact> : null}
          {e.stored_estimate !== null && e.stored_estimate !== undefined ? (
            <Fact label="Round trip">
              {Math.abs(e.stored_estimate - e.probability) < 1e-9 ? "matches the training-time estimate" : "differs from stored estimate"}
            </Fact>
          ) : null}
        </dl>
      </CardBody>
    </Card>
  );
}

function TrackRecord({ e }: { e: RecessionEstimate }) {
  type Split = { n?: number; events?: number; brier?: number | null; brier_skill?: number | null; roc_auc?: number | null; brier_reference?: number | null };
  const rows: [string, Split | undefined][] = [
    ["Development 2000–2014", e.track_record.development as Split | undefined],
    ["Held-out 2015+", e.track_record.heldout as Split | undefined],
  ];
  return (
    <Card>
      <CardHeader title="Measured track record" description="Out-of-sample walk-forward results of this model." />
      <CardBody>
        <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
          <table className="w-full min-w-[320px] text-left text-xs">
            <caption className="sr-only">Brier score, skill versus the prevalence baseline and ROC-AUC by split</caption>
            <thead>
              <tr className="border-b border-line text-fg-subtle">
                <th scope="col" className="py-2 pr-3 font-medium">Split</th>
                <th scope="col" className="py-2 pr-3 font-medium">Brier</th>
                <th scope="col" className="py-2 pr-3 font-medium">Skill vs base rate</th>
                <th scope="col" className="py-2 font-medium">ROC-AUC</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, s]) => (
                <tr key={label} className="border-b border-line/60 last:border-0">
                  <th scope="row" className="py-2 pr-3 font-normal text-fg">
                    {label}
                    <p className="text-fg-subtle">{s ? `${s.n} quarters · ${s.events} events` : "—"}</p>
                  </th>
                  <td className="tabular py-2 pr-3 font-mono">{formatMetric(s?.brier)}</td>
                  <td className={`tabular py-2 pr-3 font-mono ${s?.brier_skill !== undefined && s?.brier_skill !== null && s.brier_skill < 0 ? "text-danger" : "text-fg"}`}>
                    {formatSigned(s?.brier_skill)}
                  </td>
                  <td className="tabular py-2 font-mono">{formatMetric(s?.roc_auc, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-fg-muted">
          Brier score: mean squared error of the probability (lower is better). Skill above 0 means better than always
          predicting the historical event rate. {e.selection_note}
        </p>
      </CardBody>
    </Card>
  );
}

function RiskTimeline({ iso2, horizon, modelName }: { iso2: string; horizon: Horizon; modelName: string }) {
  const history = useRecessionHistory(iso2, horizon);
  const data = history.data;
  return (
    <ChartFrame
      title={`Risk timeline · next ${horizon} quarters`}
      description="Each point is a walk-forward estimate from a model trained only on outcomes known before that year; shaded: technical recessions in stored GDP."
      series={data ? timelineSeries(data, modelName) : []}
      shading={data ? recessionShading(data) : []}
      isLoading={history.isPending}
      error={history.error instanceof ApiError && [404, 503].includes(history.error.status) ? undefined : history.error}
      onRetry={() => void history.refetch()}
      emptyTitle="No backtested probabilities"
      emptyMessage={history.error instanceof ApiError ? history.error.message : "Historic probabilities come only from walk-forward evaluation."}
      notes={
        data ? (
          <p className="mt-3 text-xs text-fg-subtle">
            {data.note} Points before 2015 belong to the development backtest; 2015 onwards to the held-out backtest.
          </p>
        ) : null
      }
      allowKindToggle={false}
      exportName={`macropulse-${iso2.toLowerCase()}-risk-h${horizon}`}
      height={280}
    />
  );
}

function NotTrained({ error }: { error: ApiError }) {
  return (
    <EmptyState icon={<Gauge className="size-6" aria-hidden />} title="Model not trained">
      <p>{error.message}</p>
      <p className="mt-2">
        On the server: <code className="font-mono text-fg">uv run macropulse data-sync</code> then{" "}
        <code className="font-mono text-fg">uv run macropulse train</code>. No probability is shown until a model has been
        trained and evaluated.
      </p>
    </EmptyState>
  );
}

export function RecessionView() {
  const { country, asOf, params, setParam, hrefWithContext } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);
  const horizon: Horizon = params.get("h") === "4" ? 4 : 2;
  const estimate = useRecessionEstimate(selected?.iso2 ?? "", horizon, asOf);
  const otherEstimate = useRecessionEstimate(selected?.iso2 ?? "", horizon === 2 ? 4 : 2, asOf);
  const e = selected ? estimate.data : undefined;
  const err = estimate.error instanceof ApiError ? estimate.error : null;

  return (
    <>
      <PageHeader
        eyebrow="Models"
        title={selected ? `Recession risk · ${selected.name}` : "Recession risk"}
        description="Estimated probability of a technical recession — two consecutive quarters of negative real-GDP growth — within the next 2 or 4 quarters."
        meta={
          <>
            <Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>
            <Segmented
              label="Forecast horizon"
              value={String(horizon) as "2" | "4"}
              onChange={(v) => setParam("h", v === "2" ? null : v)}
              options={[
                { value: "2", label: "Next 2Q" },
                { value: "4", label: "Next 4Q" },
              ]}
            />
          </>
        }
      />

      {!selected ? (
        <CountryRequired purpose="Risk estimates are per country. Your choice is kept in the URL." />
      ) : estimate.isPending && !estimate.isError ? (
        <div className="grid gap-4 xl:grid-cols-3" aria-busy="true">
          <Skeleton className="h-[520px] rounded-card" />
          <Skeleton className="h-[520px] rounded-card xl:col-span-2" />
        </div>
      ) : err && err.code === "model_not_trained" ? (
        <NotTrained error={err} />
      ) : err && [404, 503].includes(err.status) ? (
        <EmptyState icon={<Gauge className="size-6" aria-hidden />} title="No estimate for this selection">
          {err.message}
        </EmptyState>
      ) : estimate.isError ? (
        <ErrorState error={estimate.error} onRetry={() => void estimate.refetch()} />
      ) : e ? (
        <div className="grid gap-4 xl:grid-cols-3">
          <WidgetBoundary label="Estimate">
            <EstimateCard e={e} horizon={horizon} other={otherEstimate.data} />
          </WidgetBoundary>
          <div className="min-w-0 space-y-4 xl:col-span-2">
            <WidgetBoundary label="Risk timeline">
              <RiskTimeline iso2={selected.iso2} horizon={horizon} modelName={e.model.name} />
            </WidgetBoundary>
            <Card>
              <CardHeader
                title="Why this probability?"
                description={`${e.explanation.method}. Bars to the right raise the estimate, to the left lower it.`}
                action={
                  <Link href={hrefWithContext(`/countries/${selected.iso2.toLowerCase()}`)} className="text-xs font-medium text-accent hover:underline">
                    Check the inputs →
                  </Link>
                }
              />
              <CardBody>
                <Contributions items={e.explanation.items} unit={e.explanation.unit} />
                <p className="mt-4 text-xs leading-relaxed text-fg-muted">
                  {e.explanation.note}
                  {e.explanation.intercept !== null ? ` Intercept ${formatSigned(e.explanation.intercept)} log-odds.` : ""}
                </p>
              </CardBody>
            </Card>
          </div>
          <TrackRecord e={e} />
          <Card>
            <CardHeader title="Event definition" />
            <CardBody className="space-y-3 text-sm leading-relaxed text-fg-muted">
              <p>{e.event_definition}</p>
              <p className="text-xs">
                Risk bands:{" "}
                {e.bands.map((b) => `${b.name} < ${Math.round(b.upper * 100)}%`).join(" · ").replace(/high < 100%$/, "high ≥ 50%")}
                . Bands are fixed in advance and do not imply calibrated categories.
              </p>
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Limitations" />
            <CardBody>
              <ul className="list-disc space-y-1.5 pl-4 text-sm text-fg-muted">
                {e.limitations.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-fg-subtle">
                Full diagnostics: <Link href={hrefWithContext("/lab")} className="text-accent underline underline-offset-2">ML laboratory</Link>.
              </p>
            </CardBody>
          </Card>
        </div>
      ) : null}
    </>
  );
}
