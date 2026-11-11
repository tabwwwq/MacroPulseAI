"use client";

import { ChevronLeft, ChevronRight, History } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { Replay, ReplayEpisodes } from "@macropulse/shared-types";

type Basis = Replay["basis"];

import { ChartFrame } from "@/components/charts/chart-frame";
import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { Fact } from "@/components/ui/facts";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState, Notice } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/cn";
import { useAppContext } from "@/lib/context";
import { useCountries, useCrisisPresets, useRecessionHistory, useReplay, useReplayEpisodes } from "@/lib/queries";
import { DEFAULT_REPLAY, EPISODE_STATUS, gdpSeries, OUTCOME_PENDING, quarterRange, replayMarker, VERDICTS } from "@/lib/replay";
import { BANDS, formatProbability, recessionShading, timelineSeries } from "@/lib/risk";

type Horizon = 2 | 4;
const HORIZONS = [
  { value: "2", label: "Next 2 quarters" },
  { value: "4", label: "Next 4 quarters" },
];
const BASIS_FALLBACK = "Revised-data / release-lag approximation";
const num = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });
const SPLIT_LABEL: Record<string, string> = { development: "Development year", heldout: "Held-out year", unlabelled: "Outcome pending" };

function Scrubber({ quarters, value, onChange }: { quarters: string[]; value: string; onChange: (q: string) => void }) {
  const index = Math.max(0, quarters.indexOf(value));
  const [pos, setPos] = useState(index);
  const [synced, setSynced] = useState(index);
  const timer = useRef<number | undefined>(undefined);
  // A new URL value (preset, episode link, as-of menu) moves the thumb.
  if (index !== synced) {
    setSynced(index);
    setPos(index);
  }
  useEffect(() => () => window.clearTimeout(timer.current), []);
  // Dragging moves the thumb at once and navigates once it rests for 300 ms.
  function move(next: number) {
    setPos(next);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      const q = quarters[next];
      if (q && q !== value) onChange(q);
    }, 300);
  }
  if (!quarters.length) return null;
  const shown = quarters[pos] ?? value;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor="replay-quarter" className="text-xs font-medium uppercase tracking-wider text-fg-subtle">
          Replay quarter
        </label>
        <output htmlFor="replay-quarter" className="tabular whitespace-nowrap font-mono text-lg text-accent">{shown}</output>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <Button size="icon" variant="ghost" aria-label="Previous quarter" disabled={pos <= 0} onClick={() => move(Math.max(0, pos - 1))}>
          <ChevronLeft aria-hidden />
        </Button>
        <input
          id="replay-quarter"
          type="range"
          min={0}
          max={quarters.length - 1}
          step={1}
          value={pos}
          onChange={(e) => move(Number(e.target.value))}
          aria-valuetext={shown}
          className="w-full accent-accent"
        />
        <Button size="icon" variant="ghost" aria-label="Next quarter" disabled={pos >= quarters.length - 1} onClick={() => move(Math.min(quarters.length - 1, pos + 1))}>
          <ChevronRight aria-hidden />
        </Button>
      </div>
      <div className="flex justify-between font-mono text-[11px] text-fg-subtle" aria-hidden>
        <span>{quarters[0]}</span>
        <span>{quarters.at(-1)}</span>
      </div>
    </div>
  );
}

function BasisBanner({ basis }: { basis?: Basis }) {
  return (
    <div role="note" className="rounded-xl border border-warn/40 bg-warn/[0.08] px-4 py-3 text-sm text-fg">
      <p className="font-medium">{basis?.label ?? BASIS_FALLBACK}</p>
      <p className="mt-1 text-fg-muted">
        {basis?.vintage_note ??
          "Replays use today's revised data cut at the as-of date with conservative publication lags, not the figures as first published."}
      </p>
    </div>
  );
}

function EstimateCard({ r, updating }: { r: Replay; updating: boolean }) {
  const band = BANDS[r.band] ?? { label: r.band, tone: "neutral" as const, color: "#a0abc0" };
  const verdict = r.outcome.verdict ? VERDICTS[r.outcome.verdict] : OUTCOME_PENDING;
  return (
    <Card aria-busy={updating}>
      <CardHeader
        title={`What the model said at ${r.as_of}`}
        description={`Walk-forward estimate · technical recession in the next ${r.horizon} quarters`}
        action={updating ? <Badge tone="neutral">Updating…</Badge> : <Badge tone="accent">Out of sample</Badge>}
      />
      <CardBody className="space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <span className="tabular font-mono text-4xl text-fg">{formatProbability(r.probability)}</span>
          <span className="flex gap-2">
            <Badge tone={band.tone}>{band.label}</Badge>
            {verdict ? <Badge tone={verdict.tone}>{verdict.label}</Badge> : null}
          </span>
        </div>
        <div className="relative h-2 rounded-full bg-surface-2" aria-hidden>
          <div className="h-2 rounded-full" style={{ width: `${Math.max(0.5, r.probability * 100)}%`, background: band.color }} />
          <span className="absolute inset-y-[-3px] w-px bg-fg-muted" style={{ left: `${r.threshold * 100}%` }} title="50 % line" />
        </div>
        <p className="text-sm text-fg-muted">{verdict?.text}</p>
        <dl>
          <Fact label="Base rate in the fold's training data">{formatProbability(r.baseline_probability)}</Fact>
          <Fact label="Model">{r.model.name}</Fact>
          <Fact label="Walk-forward fold">{r.model.fold_year}</Fact>
          <Fact label="Fitted on outcomes through">as-of {r.model.trained_through_as_of}</Fact>
          <Fact label="Training quarters">{r.model.training_rows ?? "—"}</Fact>
          <Fact label="Year type">{SPLIT_LABEL[r.model.split] ?? r.model.split}</Fact>
          <Fact label="Run">{r.model.run_id}</Fact>
        </dl>
        <p className="text-xs leading-relaxed text-fg-subtle">{r.model.selection_note}</p>
      </CardBody>
    </Card>
  );
}

function OutcomeCard({ r }: { r: Replay }) {
  const values = new Map(r.gdp.map((g) => [g.period, g.value]));
  return (
    <Card>
      <CardHeader title="What happened next" description={r.event_definition} />
      <CardBody className="space-y-4">
        <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4" aria-label="Outcome window, real GDP q/q as published later">
          {r.outcome.window.map((q) => {
            const v = values.get(q);
            const negative = typeof v === "number" && v < 0;
            return (
              <li key={q} className={cn("rounded-lg border p-2 text-center", negative ? "border-danger/40 bg-danger/[0.07]" : "border-line")}>
                <p className="font-mono text-[11px] text-fg-subtle">{q}</p>
                <p className={cn("tabular font-mono text-lg", negative ? "text-danger" : "text-fg")}>
                  {typeof v === "number" ? `${v > 0 ? "+" : ""}${num.format(v)} %` : "N/A"}
                </p>
                <p className="text-[11px] text-fg-subtle">{typeof v !== "number" ? "not published" : negative ? "negative" : "not negative"}</p>
              </li>
            );
          })}
        </ul>
        <p className="text-sm text-fg">
          {r.outcome.status === "observed"
            ? r.outcome.label === 1
              ? "A technical recession occurred inside the window."
              : "No technical recession inside the window."
            : r.outcome.status === "censored"
              ? "The window has not been fully published yet."
              : "GDP is missing in the window, so the outcome is unknown."}
        </p>
        {r.outcome.events.length ? (
          <p className="text-xs text-fg-muted">
            Technical recession{r.outcome.events.length > 1 ? "s" : ""} overlapping the window (today&apos;s data):{" "}
            {r.outcome.events.map((e) => `${e.start} to ${e.end}`).join("; ")}
          </p>
        ) : null}
        {r.nber ? (
          <div className="rounded-lg border border-dashed border-line-strong p-3 text-xs text-fg-muted">
            <p className="font-medium text-fg">{r.nber.name}</p>
            <p className="mt-1">
              {r.nber.months_in_window} of {r.nber.window_months} months in the window
              {r.nber.months_known < r.nber.window_months ? ` (${r.nber.months_known} published)` : ""} · {r.nber.source}. Official
              US business-cycle dates differ from the GDP rule the model is trained on.
            </p>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

function KnownInputs({ r }: { r: Replay }) {
  if (!r.inputs.length) return <EmptyState title="Inputs unavailable">{r.inputs_note}</EmptyState>;
  return (
    <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
      <table className="w-full min-w-[560px] text-left text-xs tabular">
        <caption className="sr-only">Model inputs as known at the replay date</caption>
        <thead className="text-fg-subtle">
          <tr>
            <th scope="col" className="py-2 font-medium">Input</th>
            <th scope="col" className="py-2 pl-3 text-right font-medium">Value</th>
            <th scope="col" className="whitespace-nowrap py-2 pl-3 font-medium">Reference period</th>
            <th scope="col" className="whitespace-nowrap py-2 pl-3 text-right font-medium">Lag assumed</th>
          </tr>
        </thead>
        <tbody className="font-mono text-fg">
          {r.inputs.map((i) => (
            <tr key={i.feature} className="border-t border-line/60">
              <th scope="row" className="py-1.5 font-sans font-normal text-fg-muted">{i.label}</th>
              <td className="py-1.5 pl-3 text-right">{num.format(i.value)}</td>
              <td className="whitespace-nowrap py-1.5 pl-3">
                {i.period ?? "—"}
                {i.stale ? <Badge tone="warn" className="ml-2 font-sans">older month</Badge> : null}
              </td>
              <td className="py-1.5 pl-3 text-right text-fg-subtle">{i.publication_lag_days} d</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EpisodesCard({ e, onReplay }: { e: ReplayEpisodes; onReplay: (q: string) => void }) {
  const evaluable = e.recessions.filter((r) => r.status !== "not_evaluable");
  const earlier = e.recessions.length - evaluable.length;
  const c = e.confusion;
  return (
    <Card>
      <CardHeader
        title="Warnings, misses and false alarms"
        description={`Walk-forward estimates from ${e.first_as_of} · ${e.model_name} · 50 % line`}
      />
      <CardBody className="space-y-5">
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Recession quarters flagged", c.tp ?? 0, (c.tp ?? 0) + (c.fn ?? 0)],
            ["Recession quarters missed", c.fn ?? 0, (c.tp ?? 0) + (c.fn ?? 0)],
            ["False-alarm quarters", c.fp ?? 0, (c.fp ?? 0) + (c.tn ?? 0)],
            ["Correctly quiet quarters", c.tn ?? 0, (c.fp ?? 0) + (c.tn ?? 0)],
          ].map(([label, n, of]) => (
            <div key={label as string} className="rounded-lg border border-line p-3">
              <dt className="text-[11px] text-fg-subtle">{label}</dt>
              <dd className="tabular mt-1 font-mono text-lg text-fg">
                {n} <span className="text-xs text-fg-subtle">of {of}</span>
              </dd>
            </div>
          ))}
        </dl>
        <div>
          <h3 className="text-sm font-medium text-fg">Realised technical recessions</h3>
          {evaluable.length ? (
            <ul className="mt-2 divide-y divide-line/60">
              {evaluable.map((r) => {
                const meta = EPISODE_STATUS[r.status] ?? { label: r.status, tone: "neutral" as const };
                return (
                  <li key={r.start} className="flex flex-wrap items-center justify-between gap-2 py-2 text-xs">
                    <span className="font-mono text-fg">{r.start} to {r.end}</span>
                    <span className="flex items-center gap-2 text-fg-muted">
                      highest beforehand {formatProbability(r.max_probability)} ({r.max_at})
                      <Badge tone={meta.tone}>{meta.label}</Badge>
                      {r.max_at ? (
                        <Button size="sm" variant="ghost" onClick={() => onReplay(r.max_at as string)} aria-label={`Replay ${r.max_at}`}>
                          Replay
                        </Button>
                      ) : null}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-fg-subtle">No technical recession since {e.first_as_of} can be evaluated.</p>
          )}
          {earlier ? (
            <p className="mt-2 text-xs text-fg-subtle">
              {earlier} earlier recession{earlier > 1 ? "s" : ""} before {e.first_as_of}: not evaluable out of sample.
            </p>
          ) : null}
        </div>
        <div>
          <h3 className="text-sm font-medium text-fg">False alarms</h3>
          {e.false_alarms.length ? (
            <ul className="mt-2 divide-y divide-line/60">
              {e.false_alarms.map((f) => (
                <li key={f.start} className="flex flex-wrap items-center justify-between gap-2 py-2 text-xs">
                  <span className="font-mono text-fg">
                    {f.start === f.end ? f.start : `${f.start} to ${f.end}`}
                    <span className="ml-2 font-sans text-fg-subtle">{f.quarters} quarter{f.quarters > 1 ? "s" : ""}</span>
                  </span>
                  <span className="flex items-center gap-2 text-fg-muted">
                    up to {formatProbability(f.max_probability)}
                    {f.follows_recession ? <span className="text-fg-subtle">· right after the {f.follows_recession} recession</span> : null}
                    <Button size="sm" variant="ghost" onClick={() => onReplay(f.max_at)} aria-label={`Replay ${f.max_at}`}>
                      Replay
                    </Button>
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-fg-subtle">No walk-forward estimate reached 50 % without a recession following.</p>
          )}
        </div>
        <p className="text-xs leading-relaxed text-fg-subtle">{e.note}</p>
      </CardBody>
    </Card>
  );
}

function HistoryBody({ iso2 }: { iso2: string }) {
  const { asOf, params, setParam, setAsOf } = useAppContext();
  const horizon: Horizon = params.get("horizon") === "2" ? 2 : 4;
  const quarter = asOf ?? DEFAULT_REPLAY;
  const presets = useCrisisPresets();
  const episodes = useReplayEpisodes(iso2, horizon);
  const replay = useReplay(iso2, horizon, quarter);
  const history = useRecessionHistory(iso2, horizon);
  const quarters = useMemo(
    () => (episodes.data ? quarterRange(episodes.data.first_as_of, episodes.data.last_as_of) : []),
    [episodes.data],
  );
  const answer = replay.error instanceof ApiError && [404, 422, 503].includes(replay.error.status) ? replay.error : null;
  /** Episode links sit far below the result: replay that quarter and bring the result into view. */
  function jump(q: string) {
    setAsOf(q);
    const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.getElementById("replay-result")?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
  }
  const r = answer ? undefined : replay.data;
  const timeline = useMemo(
    () => (history.data ? timelineSeries(history.data, history.data.model_name).filter((s) => s.id !== "current") : []),
    [history.data],
  );
  const shading = useMemo(
    () => (history.data ? [...recessionShading(history.data), replayMarker(quarter)] : [replayMarker(quarter)]),
    [history.data, quarter],
  );

  return (
    <div className="space-y-4">
      <BasisBanner basis={r?.basis} />
      <Card>
        <CardBody className="space-y-5 pt-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:gap-8">
            <div className="shrink-0">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Horizon</p>
              <Segmented label="Recession horizon" options={HORIZONS} value={String(horizon)} onChange={(v) => setParam("horizon", v)} />
            </div>
            {presets.data?.length ? (
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Crisis dates</p>
                <div className="flex flex-wrap gap-2">
                  {presets.data.map((p) => (
                    <Button key={p.as_of} size="sm" variant={p.as_of === quarter ? "primary" : "secondary"} aria-pressed={p.as_of === quarter} onClick={() => setAsOf(p.as_of)}>
                      {p.label} · {p.as_of}
                    </Button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
          <Scrubber quarters={quarters} value={quarter} onChange={setAsOf} />
        </CardBody>
      </Card>
      {!asOf ? (
        <Notice>No as-of quarter selected, so this shows {DEFAULT_REPLAY}. Pick a crisis date, drag the scrubber or use the as-of menu.</Notice>
      ) : null}

      <div id="replay-result" className="scroll-mt-20" />
      {replay.isPending ? (
        <div className="grid gap-4 xl:grid-cols-2" role="status" aria-label="Loading replay">
          <Skeleton className="h-[420px] rounded-card" />
          <Skeleton className="h-[420px] rounded-card" />
        </div>
      ) : answer ? (
        <EmptyState icon={<History className="size-6" aria-hidden />} title={answer.status === 503 ? "Model not available" : `No replay for ${quarter}`}>
          {answer.message}
        </EmptyState>
      ) : replay.error || !r ? (
        <ErrorState error={replay.error} onRetry={() => void replay.refetch()} />
      ) : (
        <>
          <div className="grid gap-4 xl:grid-cols-2">
            <EstimateCard r={r} updating={replay.isFetching} />
            <OutcomeCard r={r} />
          </div>
          <div className="grid gap-4 xl:grid-cols-5">
            <Card className="xl:col-span-3">
              <CardHeader title={`Known on ${r.cutoff}`} description="Each input as it could be known at the cut-off: period ended and the assumed publication lag passed." />
              <CardBody>
                <KnownInputs r={r} />
              </CardBody>
            </Card>
            <div className="min-w-0 xl:col-span-2">
              <WidgetBoundary label="GDP before and after">
                <ChartFrame
                  title="Real GDP growth around the replay date"
                  description="Bars: q/q growth published by the as-of (today's revised values) and published later."
                  series={gdpSeries(r)}
                  defaultKind="bar"
                  exportName={`macropulse-${iso2.toLowerCase()}-replay-${r.as_of}-gdp`}
                  height={260}
                />
              </WidgetBoundary>
            </div>
          </div>
        </>
      )}

      <WidgetBoundary label="Walk-forward timeline">
        <ChartFrame
          title="Walk-forward risk timeline"
          description="Each point is an estimate made without later outcomes; shaded bands are realised technical recessions (today's data); the marked quarter is the replay date."
          series={timeline}
          shading={shading}
          isLoading={history.isPending}
          error={history.error instanceof ApiError && [404, 503].includes(history.error.status) ? undefined : history.error}
          onRetry={() => void history.refetch()}
          emptyTitle="No walk-forward history"
          emptyMessage={history.error instanceof ApiError ? history.error.message : undefined}
          exportName={`macropulse-${iso2.toLowerCase()}-walk-forward-h${horizon}`}
          height={280}
        />
      </WidgetBoundary>

      {episodes.data ? <EpisodesCard e={episodes.data} onReplay={jump} /> : episodes.isPending ? <Skeleton className="h-64 rounded-card" /> : null}

      {r ? (
        <Card>
          <CardHeader title="How to read a replay" description="What this page can and cannot show." />
          <CardBody>
            <ul className="list-disc space-y-1.5 pl-4 text-xs leading-relaxed text-fg-muted">
              {r.caveats.map((c) => (
                <li key={c}>{c}</li>
              ))}
              <li>{r.basis.detail}</li>
            </ul>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

export function HistoryView() {
  const { country } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);

  return (
    <>
      <PageHeader
        eyebrow="Models"
        title="Crisis time machine"
        description="Pick a past quarter and see what the walk-forward model said with only the data published by then, next to what happened afterwards."
        meta={<Badge tone="warn">{BASIS_FALLBACK}</Badge>}
      />
      {!selected ? (
        <div className="space-y-4">
          <BasisBanner />
          <CountryRequired purpose="Replays are per country." />
        </div>
      ) : (
        <HistoryBody key={selected.iso2} iso2={selected.iso2} />
      )}
    </>
  );
}
