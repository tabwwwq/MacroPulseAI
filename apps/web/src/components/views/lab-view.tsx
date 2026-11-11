"use client";

import { FlaskConical, TriangleExclamationPoint } from "lucide-react";
import type { ReactNode } from "react";

import type { MetricValue, ModelDetail, ModelSummary, SplitCurves } from "@macropulse/shared-types";

import { XYChart, type XYSeries } from "@/components/charts/xy-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { useAppContext } from "@/lib/context";
import { formatDateTimeUtc } from "@/lib/format";
import { useModelCurves, useModelDetail, useModels } from "@/lib/queries";
import { formatMetric, formatSigned } from "@/lib/risk";

type Horizon = 2 | 4;
const SPLITS = [
  { key: "development", label: "Development 2000–2014" },
  { key: "heldout", label: "Held-out 2015+" },
] as const;

interface CalibrationBin {
  bin: [number, number];
  count: number;
  mean_predicted: number | null;
  observed_rate: number | null;
  events: number;
}

function headline(m: ModelSummary, split: string, metric: string): number | null | undefined {
  return m.headline[split]?.[metric];
}

function metric(detail: ModelDetail, split: string, name: string, segment = "all"): MetricValue | undefined {
  return detail.metrics.find((m) => m.split === split && m.segment === segment && m.metric === name);
}

function Cell({ value, digits = 3, signed = false, note }: { value: number | null | undefined; digits?: number; signed?: boolean; note?: string | null }) {
  const text = signed ? formatSigned(value) : formatMetric(value, digits);
  const negative = signed && typeof value === "number" && value < 0;
  return (
    <td className={`tabular whitespace-nowrap py-2 pr-3 font-mono text-xs ${negative ? "text-danger" : value == null ? "text-fg-subtle" : "text-fg"}`} title={note ?? undefined}>
      {text}
    </td>
  );
}

function Comparison({ models, selectedKey, onInspect }: { models: ModelSummary[]; selectedKey: string; onInspect: (key: string) => void }) {
  return (
    <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
      <table className="w-full min-w-[900px] text-left text-sm">
        <caption className="sr-only">Out-of-sample metrics of every model of this run and horizon</caption>
        <thead>
          <tr className="border-b border-line text-xs text-fg-subtle">
            <th scope="col" rowSpan={2} className="py-2 pr-3 align-bottom font-medium">Model</th>
            {SPLITS.map((s) => (
              <th key={s.key} scope="colgroup" colSpan={4} className="pb-1 pr-3 pt-2 font-medium">
                {s.label}
              </th>
            ))}
            <th scope="col" rowSpan={2} className="py-2 align-bottom font-medium">
              <span className="sr-only">Inspect</span>
            </th>
          </tr>
          <tr className="border-b border-line text-[11px] text-fg-subtle">
            {SPLITS.flatMap((s) =>
              ["Brier", "Skill", "ROC-AUC", "PR-AUC"].map((h) => (
                <th key={`${s.key}-${h}`} scope="col" className="pb-2 pr-3 font-medium">
                  {h}
                </th>
              )),
            )}
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.id} className={`border-b border-line/60 align-top last:border-0 ${m.model_key === selectedKey ? "bg-accent/[0.05]" : ""}`}>
              <th scope="row" className="py-2 pr-3 font-normal">
                <p className="text-fg">{m.name}</p>
                <p className="mt-1 flex flex-wrap gap-1.5">
                  <Badge tone="neutral" dashed>{m.role}</Badge>
                  {m.selected ? <Badge tone="accent">published</Badge> : null}
                  {m.status !== "evaluated" ? <Badge tone="warn">not run</Badge> : null}
                </p>
                {m.unavailable_reason ? <p className="mt-1 text-xs text-fg-subtle">{m.unavailable_reason}</p> : null}
              </th>
              {SPLITS.flatMap((s) => [
                <Cell key={`${s.key}-b`} value={headline(m, s.key, "brier")} />,
                <Cell key={`${s.key}-s`} value={headline(m, s.key, "brier_skill")} signed />,
                <Cell key={`${s.key}-r`} value={headline(m, s.key, "roc_auc")} digits={2} />,
                <Cell key={`${s.key}-p`} value={headline(m, s.key, "pr_auc")} digits={2} />,
              ])}
              <td className="py-2">
                {m.status === "evaluated" ? (
                  <Button size="sm" variant={m.model_key === selectedKey ? "secondary" : "ghost"} aria-pressed={m.model_key === selectedKey} onClick={() => onInspect(m.model_key)}>
                    Inspect
                  </Button>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function curveSeries(curves: SplitCurves[], kind: "roc" | "pr"): XYSeries[] {
  return curves.flatMap((c) =>
    c[kind] ? [{ name: `${c.split === "development" ? "Dev" : "Held-out"} ${c.events}/${c.n}`, points: c[kind] ?? [], step: kind === "pr" }] : [],
  );
}

function ChartCard({ title, description, children, notes }: { title: string; description: string; children: ReactNode; notes?: ReactNode }) {
  return (
    <Card>
      <CardHeader title={title} description={description} />
      <CardBody>
        {children}
        {notes}
      </CardBody>
    </Card>
  );
}

function Confusion({ detail }: { detail: ModelDetail }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {SPLITS.map((s) => {
        const c = metric(detail, s.key, "confusion")?.detail as { tp: number; fp: number; fn: number; tn: number } | undefined;
        const precision = metric(detail, s.key, "precision");
        const recall = metric(detail, s.key, "recall");
        const accuracy = metric(detail, s.key, "accuracy");
        return (
          <div key={s.key}>
            <p className="mb-2 text-xs font-medium text-fg">{s.label}</p>
            {c ? (
              <table className="w-full text-center text-xs">
                <caption className="sr-only">Confusion matrix at probability threshold 0.5, {s.label}</caption>
                <thead>
                  <tr className="text-fg-subtle">
                    <th scope="col" className="py-1 font-medium" />
                    <th scope="col" className="py-1 font-medium">Predicted event</th>
                    <th scope="col" className="py-1 font-medium">Predicted none</th>
                  </tr>
                </thead>
                <tbody className="tabular font-mono">
                  <tr>
                    <th scope="row" className="py-1.5 text-left font-medium text-fg-subtle">Event</th>
                    <td className="rounded bg-ok/10 py-1.5 text-fg">{c.tp}</td>
                    <td className="rounded bg-danger/10 py-1.5 text-fg">{c.fn}</td>
                  </tr>
                  <tr>
                    <th scope="row" className="py-1.5 text-left font-medium text-fg-subtle">No event</th>
                    <td className="rounded bg-warn/10 py-1.5 text-fg">{c.fp}</td>
                    <td className="rounded bg-surface-2 py-1.5 text-fg">{c.tn}</td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <p className="text-xs text-fg-subtle">N/A</p>
            )}
            <p className="mt-2 font-mono text-[11px] text-fg-muted">
              precision {formatMetric(precision?.value, 2)}
              {precision?.note ? ` (${precision.note})` : ""} · recall {formatMetric(recall?.value, 2)} · accuracy{" "}
              {formatMetric(accuracy?.value, 2)}
            </p>
          </div>
        );
      })}
    </div>
  );
}

function PerCountry({ detail }: { detail: ModelDetail }) {
  const countries = [...new Set(detail.metrics.filter((m) => m.segment !== "all").map((m) => m.segment))].sort();
  return (
    <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
      <table className="w-full min-w-[560px] text-left text-xs">
        <caption className="sr-only">Brier score and skill per country and split</caption>
        <thead>
          <tr className="border-b border-line text-fg-subtle">
            <th scope="col" className="py-2 pr-3 font-medium">Country</th>
            {SPLITS.map((s) => (
              <th key={s.key} scope="col" className="py-2 pr-3 font-medium">
                {s.label}: Brier · skill · events/n
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {countries.map((c) => (
            <tr key={c} className="border-b border-line/60 last:border-0">
              <th scope="row" className="py-2 pr-3 font-mono text-fg">{c}</th>
              {SPLITS.map((s) => {
                const b = metric(detail, s.key, "brier", c);
                const k = metric(detail, s.key, "brier_skill", c);
                return (
                  <td key={s.key} className="tabular py-2 pr-3 font-mono">
                    {formatMetric(b?.value)} · <span className={k?.value != null && k.value < 0 ? "text-danger" : ""}>{formatSigned(k?.value)}</span> ·{" "}
                    {b ? `${b.events}/${b.n}` : "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FoldTimeline({ detail }: { detail: ModelDetail }) {
  const folds = (detail.evaluation.folds ?? []) as { year: number; train_rows: number; test_rows: number }[];
  const skipped = (detail.evaluation.skipped_folds ?? []) as string[];
  const max = Math.max(...folds.map((f) => f.train_rows), 1);
  return (
    <div>
      <ol className="space-y-1" aria-label="Walk-forward folds">
        {folds.map((f) => (
          <li key={f.year} className="grid grid-cols-[2.75rem_1fr_auto] items-center gap-2 text-[11px]">
            <span className="tabular font-mono text-fg-muted">{f.year}</span>
            <span className="relative h-2 rounded-full bg-canvas" aria-hidden>
              <span className={`absolute inset-y-0 left-0 rounded-full ${f.year <= 2014 ? "bg-accent/60" : "bg-warn/70"}`} style={{ width: `${(f.train_rows / max) * 100}%` }} />
            </span>
            <span className="tabular whitespace-nowrap font-mono text-fg-subtle">
              {f.train_rows}/{f.test_rows}
            </span>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-xs leading-relaxed text-fg-muted">
        {String(detail.evaluation.method ?? "")}. Purge: {String(detail.evaluation.purge ?? "")}. Blue folds form the development
        backtest, amber the held-out one; numbers are training/test rows.
        {skipped.length ? ` Skipped: ${skipped.join("; ")}.` : ""}
      </p>
    </div>
  );
}

function Coefficients({ coefficients, labels }: { coefficients: Record<string, number>; labels: Record<string, string> }) {
  const entries = Object.entries(coefficients).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const max = Math.max(...entries.map(([, v]) => Math.abs(v)), 1e-9);
  return (
    <ul className="space-y-2" aria-label="Standardised logistic coefficients">
      {entries.map(([name, v]) => (
        <li key={name}>
          <div className="flex justify-between gap-3 text-xs">
            <span className="text-fg">{labels[name] ?? name}</span>
            <span className="tabular font-mono text-fg-muted">{formatSigned(v)}</span>
          </div>
          <div className="relative mt-1 h-1.5 rounded-full bg-canvas" aria-hidden>
            <span className="absolute inset-y-0 left-1/2 w-px bg-line-strong" />
            <span className="absolute inset-y-0 rounded-full" style={{ width: `${(Math.abs(v) / max) * 50}%`, left: v > 0 ? "50%" : undefined, right: v > 0 ? undefined : "50%", background: v > 0 ? "linear-gradient(90deg, #f5b54466, #f5b544)" : "linear-gradient(270deg, #4cc3ff66, #4cc3ff)" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function Reproducibility({ d }: { d: ModelDetail }) {
  const rows: [string, ReactNode][] = [
    ["Model version", d.id],
    ["Training run", d.run_id],
    ["Trained", formatDateTimeUtc(d.created_at)],
    ["Command", d.command],
    ["Seed", d.seed],
    ["Code revision", d.code_revision ?? "unknown"],
    ["Data snapshot", d.data_snapshot],
    ["Target / features", `${d.target_version} · ${d.feature_set_version}`],
    ["Training sample", d.training_rows ? `${d.training_rows} quarters · ${d.training_events} events · labels to ${d.training_last_as_of}` : "backtest folds only (not the published model)"],
    ["Artifact", d.artifact_available ? "saved (models/artifacts)" : "not saved"],
    ["Libraries", Object.entries(d.library_versions).map(([k, v]) => `${k} ${String(v)}`).join(" · ")],
    ["Hyperparameters", Object.entries(d.params).map(([k, v]) => `${k}=${String(v)}`).join(", ") || "—"],
  ];
  return (
    <dl className="space-y-1.5 text-xs">
      {rows.map(([k, v]) => (
        <div key={k} className="grid gap-1 sm:grid-cols-[9rem_1fr]">
          <dt className="text-fg-subtle">{k}</dt>
          <dd className="min-w-0 break-words font-mono text-fg">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function LabView() {
  const { params, setParam } = useAppContext();
  const models = useModels();
  const horizon: Horizon = params.get("h") === "4" ? 4 : 2;
  const items = (models.data?.items ?? []).filter((m) => m.horizon === horizon);
  const published = items.find((m) => m.selected);
  const requested = params.get("model");
  const current = items.find((m) => m.model_key === requested && m.status === "evaluated") ?? published;
  const detail = useModelDetail(current?.id ?? null);
  const curves = useModelCurves(current?.id ?? null);
  const logisticId = items.find((m) => m.model_key === "logistic")?.id ?? null;
  const logistic = useModelDetail(logisticId);
  const d = detail.data;
  const featureLabels = (d?.evaluation.features ?? {}) as Record<string, string>;

  const calibration: XYSeries[] = d
    ? [
        { name: "Ideal", points: [{ x: 0, y: 0 }, { x: 1, y: 1 }], dashed: true },
        ...SPLITS.flatMap((s) => {
          const bins = (metric(d, s.key, "calibration")?.detail ?? []) as CalibrationBin[];
          const points = bins.filter((b) => b.count && b.mean_predicted !== null && b.observed_rate !== null).map((b) => ({ x: b.mean_predicted as number, y: b.observed_rate as number }));
          return points.length ? [{ name: s.key === "development" ? "Dev" : "Held-out", points, markers: true }] : [];
        }),
      ]
    : [];
  const heldout = published ? (published.heldout_check as { evaluated?: boolean; beats_prevalence?: boolean; brier_skill?: number } | null) : null;

  return (
    <>
      <PageHeader
        eyebrow="Platform"
        title="ML laboratory"
        description="Every model of the latest training run, evaluated out of sample with yearly walk-forward folds — baselines included, nothing hidden."
        meta={
          <>
            {models.data?.run_id ? <Badge tone="neutral">Run {models.data.run_id}</Badge> : null}
            <Segmented
              label="Horizon"
              value={String(horizon) as "2" | "4"}
              onChange={(v) => setParam("h", v === "2" ? null : v)}
              options={[
                { value: "2", label: "2 quarters" },
                { value: "4", label: "4 quarters" },
              ]}
            />
          </>
        }
      />

      {models.isPending ? (
        <Skeleton className="h-96 w-full rounded-card" />
      ) : models.isError ? (
        <ErrorState error={models.error} onRetry={() => void models.refetch()} />
      ) : !items.length ? (
        <EmptyState icon={<FlaskConical className="size-6" aria-hidden />} title="No trained models">
          {models.data.note} Steps: <code className="font-mono text-fg">uv run macropulse data-sync</code>, then{" "}
          <code className="font-mono text-fg">uv run macropulse train</code>.
        </EmptyState>
      ) : (
        <div className="space-y-4">
          <Card>
            <CardHeader title={`Model comparison · ${horizon} quarters ahead`} description="Brier score (lower is better) and Brier skill against the prevalence baseline (above 0 beats it). Hover N/A for the reason." />
            <CardBody>
              {published?.selection_note ? <p className="mb-3 text-sm text-fg-muted">{published.selection_note}</p> : null}
              {heldout?.evaluated && !heldout.beats_prevalence ? (
                <div role="note" className="mb-4 flex gap-2 rounded-lg border border-warn/30 bg-warn/[0.07] p-3 text-xs text-fg-muted">
                  <TriangleExclamationPoint className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
                  <span>
                    The published model does <strong className="text-fg">not</strong> beat the base rate on the held-out years (Brier
                    skill {formatSigned(heldout.brier_skill)}). The choice was made on development data only; held-out results were never
                    used to pick a model.
                  </span>
                </div>
              ) : null}
              <Comparison models={items} selectedKey={current?.model_key ?? ""} onInspect={(key) => setParam("model", key === published?.model_key ? null : key)} />
            </CardBody>
          </Card>

          {!d ? (
            detail.isError ? <ErrorState error={detail.error} onRetry={() => void detail.refetch()} /> : <Skeleton className="h-72 w-full rounded-card" />
          ) : (
            <>
              <h2 className="pt-2 text-sm font-medium text-fg">
                Inspecting: {d.name} {d.selected ? <Badge tone="accent">published</Badge> : null}
              </h2>
              <div className="grid gap-4 lg:grid-cols-3">
                <WidgetBoundary label="Calibration">
                  <ChartCard title="Calibration" description="Mean predicted probability vs observed event rate per bin (0–0.1, 0.1–0.2, 0.2–0.4, 0.4–0.6, 0.6–1).">
                    <XYChart series={calibration} xLabel="Predicted" yLabel="Observed" ariaLabel={`Calibration of ${d.name}`} />
                  </ChartCard>
                </WidgetBoundary>
                <WidgetBoundary label="ROC curve">
                  <ChartCard
                    title="ROC curve"
                    description="Recall vs false-positive rate over all thresholds."
                    notes={curves.data?.splits.filter((s) => !s.roc).map((s) => <p key={s.split} className="mt-2 text-xs text-fg-subtle">{s.split}: {s.note}</p>)}
                  >
                    <XYChart
                      series={[{ name: "Chance", points: [{ x: 0, y: 0 }, { x: 1, y: 1 }], dashed: true }, ...curveSeries(curves.data?.splits ?? [], "roc")]}
                      xLabel="False-positive rate"
                      yLabel="Recall"
                      ariaLabel={`ROC curves of ${d.name}`}
                    />
                  </ChartCard>
                </WidgetBoundary>
                <WidgetBoundary label="Precision-recall curve">
                  <ChartCard title="Precision–recall" description="What fraction of alarms were real, at each recall level. The baseline equals the event rate.">
                    <XYChart series={curveSeries(curves.data?.splits ?? [], "pr")} xLabel="Recall" yLabel="Precision" ariaLabel={`Precision-recall curves of ${d.name}`} />
                  </ChartCard>
                </WidgetBoundary>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                  <CardHeader title="Confusion matrix · threshold 0.5" description="An alarm is raised when the probability is at least 50% (more likely than not). Accuracy is shown only for completeness: with few events it looks good even for a useless model." />
                  <CardBody>
                    <Confusion detail={d} />
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader title="By country" description="Same out-of-sample predictions, split per country." />
                  <CardBody>
                    <PerCountry detail={d} />
                  </CardBody>
                </Card>
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <Card>
                  <CardHeader title="Walk-forward folds" description="One fold per calendar year; training rows grow over time." />
                  <CardBody>
                    <FoldTimeline detail={d} />
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader
                    title="Global explanation"
                    description="Standardised logistic-regression coefficients on the full labelled sample (per one standard deviation, in log-odds). SHAP is not installed."
                  />
                  <CardBody>
                    {logistic.data?.coefficients ? (
                      <Coefficients coefficients={logistic.data.coefficients as Record<string, number>} labels={featureLabels} />
                    ) : (
                      <p className="text-sm text-fg-subtle">No logistic model in this run.</p>
                    )}
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader title="Reproducibility" description="Everything needed to re-run this exact model." />
                  <CardBody>
                    <Reproducibility d={d} />
                  </CardBody>
                </Card>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
