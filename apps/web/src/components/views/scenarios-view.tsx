"use client";

import { FileDown, RotateCcw, Save, SlidersHorizontal, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ScenarioContribution, ScenarioRequest, ScenarioResult, ShockSpec } from "@macropulse/shared-types";

import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Fact, Warning } from "@/components/ui/facts";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { formatAsOf } from "@/lib/as-of";
import { cn } from "@/lib/cn";
import { useAppContext } from "@/lib/context";
import { downloadText } from "@/lib/export";
import { formatDateTimeUtc } from "@/lib/format";
import { useCountries, useScenarioEvaluation, useScenarioSpec } from "@/lib/queries";
import { BANDS, formatProbability, formatSigned } from "@/lib/risk";
import {
  describeShocks,
  formatDeltaPp,
  formatShock,
  isUnshocked,
  loadSaved,
  parseShocks,
  type SavedScenario,
  scenarioExport,
  serializeShocks,
  type Shocks,
  storeSaved,
  toRequestShocks,
  toSaved,
  withinSpec,
} from "@/lib/scenario";
import { useDebouncedValue } from "@/lib/use-debounced";
import { useHydrated } from "@/lib/use-hydrated";

const FALLBACK_DISCLAIMER = "Exploratory model sensitivity analysis, not a causal economic simulation.";
const HORIZONS = [
  { value: "2", label: "Next 2 quarters" },
  { value: "4", label: "Next 4 quarters" },
];
const value2 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });

function fmt(v: number | null | undefined): string {
  return typeof v === "number" && Number.isFinite(v) ? value2.format(v) : "—";
}

function ShockSlider({ spec, value, onChange }: { spec: ShockSpec; value: number; onChange: (v: number) => void }) {
  const id = `shock-${spec.key}`;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="text-sm text-fg">{spec.label}</label>
        <output htmlFor={id} className={cn("tabular font-mono text-sm", value === 0 ? "text-fg-subtle" : "text-accent")}>
          {formatShock(value, spec.unit)}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={spec.minimum}
        max={spec.maximum}
        step={spec.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={formatShock(value, spec.unit)}
        className="mt-2 w-full accent-accent"
      />
      <div className="flex justify-between font-mono text-[11px] text-fg-subtle" aria-hidden>
        <span>{formatShock(spec.minimum, spec.unit)}</span>
        <span>{formatShock(spec.maximum, spec.unit)}</span>
      </div>
      <p className="mt-1 text-[11px] leading-relaxed text-fg-subtle">{spec.effect}</p>
    </div>
  );
}

function ProbabilityBar({ label, probability, band }: { label: string; probability: number; band: string }) {
  const meta = BANDS[band] ?? { label: band, tone: "neutral" as const, color: "#a0abc0" };
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-xs text-fg-subtle">{label}</span>
        <span className="flex items-center gap-2">
          <span className="tabular font-mono text-2xl text-fg">{formatProbability(probability)}</span>
          <Badge tone={meta.tone}>{meta.label}</Badge>
        </span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-surface-2" aria-hidden>
        <div className="h-2 rounded-full" style={{ width: `${Math.max(0.5, probability * 100)}%`, background: meta.color }} />
      </div>
    </div>
  );
}

function ResultCard({ r, updating }: { r: ScenarioResult; updating: boolean }) {
  const joint = r.joint_check as { available?: boolean; baseline_distance?: number; scenario_distance?: number; threshold_99?: number; unusual_combination?: boolean };
  return (
    <Card aria-busy={updating}>
      <CardHeader
        title={`Technical-recession probability · next ${r.horizon} quarters`}
        description={`${r.country} as of ${r.as_of} · published model ${r.model.name}`}
        action={updating ? <Badge tone="neutral">Updating…</Badge> : <Badge tone="accent">Sensitivity</Badge>}
      />
      <CardBody className="space-y-4">
        <ProbabilityBar label="Baseline (published inputs)" probability={r.baseline.probability} band={r.baseline.band} />
        <ProbabilityBar label="Scenario (shocked inputs)" probability={r.scenario.probability} band={r.scenario.band} />
        <p className="flex items-baseline justify-between border-t border-line pt-3 text-sm">
          <span className="text-fg-muted">Change in the model&apos;s probability</span>
          <span className={cn("tabular font-mono text-lg", r.delta > 0 ? "text-warn" : r.delta < 0 ? "text-accent" : "text-fg")}>
            {formatDeltaPp(r.delta)}
          </span>
        </p>
        {r.warnings.map((w) => (
          <Warning key={w}>{w}</Warning>
        ))}
        <dl>
          <Fact label="Model version">{r.model.id}</Fact>
          <Fact label="Explanation">{r.explanation_method}</Fact>
          <Fact label="Distance from training data">
            {joint.available
              ? `${fmt(joint.baseline_distance)} → ${fmt(joint.scenario_distance)} (99 % line ${fmt(joint.threshold_99)})`
              : "not available"}
          </Fact>
          <Fact label="Computed">{formatDateTimeUtc(r.computed_at)}</Fact>
        </dl>
      </CardBody>
    </Card>
  );
}

function DeltaList({ items, unit }: { items: ScenarioContribution[]; unit: string }) {
  const moved = items.filter((c) => Math.abs(c.delta) > 1e-9);
  const max = Math.max(...moved.map((c) => Math.abs(c.delta)), 1e-9);
  if (!moved.length) return <p className="text-sm text-fg-muted">No contribution changes: move a slider to see which model inputs respond.</p>;
  return (
    <>
      <ul className="space-y-2.5" aria-label="Change in feature contributions">
        {moved.map((c) => {
          const up = c.delta > 0;
          return (
            <li key={c.feature}>
              <div className="flex items-baseline justify-between gap-3 text-xs">
                <span className="min-w-0 text-fg">{c.label}</span>
                <span className="tabular shrink-0 font-mono text-fg-muted">
                  {formatSigned(c.delta)} <span className="text-fg-subtle">{unit}</span>
                  <span className="sr-only">{up ? ", raises the estimate" : ", lowers the estimate"}</span>
                </span>
              </div>
              <div className="relative mt-1 h-2 rounded-full bg-surface-2" aria-hidden>
                <span className="absolute inset-y-0 left-1/2 w-px bg-line-strong" />
                <span
                  className="absolute inset-y-0 rounded-full"
                  style={{ width: `${(Math.abs(c.delta) / max) * 50}%`, left: up ? "50%" : undefined, right: up ? undefined : "50%", background: up ? "#f5b544" : "#4cc3ff" }}
                />
              </div>
              <p className="mt-1 font-mono text-[11px] text-fg-subtle">
                {formatSigned(c.baseline)} → {formatSigned(c.scenario)}
              </p>
            </li>
          );
        })}
      </ul>
      {items.length > moved.length ? (
        <p className="mt-3 text-xs text-fg-subtle">{items.length - moved.length} other inputs unchanged.</p>
      ) : null}
    </>
  );
}

function InputsTable({ r }: { r: ScenarioResult }) {
  return (
    <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
      <table className="w-full min-w-[680px] text-left text-xs tabular">
        <caption className="sr-only">Model inputs, baseline and scenario, against the training range</caption>
        <thead className="text-fg-subtle">
          <tr>
            <th scope="col" className="py-2 font-medium">Input</th>
            <th scope="col" className="py-2 pl-3 text-right font-medium">Baseline</th>
            <th scope="col" className="py-2 pl-3 text-right font-medium">Scenario</th>
            <th scope="col" className="whitespace-nowrap py-2 pl-3 text-right font-medium">Training range</th>
            <th scope="col" className="py-2 pl-3 font-medium">Check</th>
          </tr>
        </thead>
        <tbody className="font-mono text-fg">
          {r.inputs.map((i) => (
            <tr key={i.feature} className={cn("border-t border-line/60", i.changed && "bg-accent/[0.05]")}>
              <th scope="row" className="py-1.5 font-sans font-normal text-fg-muted">{i.label}</th>
              <td className="py-1.5 pl-3 text-right">{fmt(i.baseline)}</td>
              <td className={cn("py-1.5 pl-3 text-right", i.changed ? "text-accent" : "text-fg-muted")}>{fmt(i.scenario)}</td>
              <td className="whitespace-nowrap py-1.5 pl-3 text-right text-fg-subtle">
                {fmt(i.training_min)} to {fmt(i.training_max)}
              </td>
              <td className="whitespace-nowrap py-1.5 pl-3 font-sans">
                {i.outside_training_range ? (
                  <Badge tone="danger">outside training range</Badge>
                ) : i.unusual ? (
                  <Badge tone="warn">unusual (outside 5–95 %)</Badge>
                ) : (
                  <span className="text-fg-subtle">within range</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SavedList({
  items, spec, onLoad, onDelete,
}: { items: SavedScenario[]; spec: ShockSpec[]; onLoad: (s: SavedScenario) => void; onDelete: (id: string) => void }) {
  if (!items.length) return <p className="text-xs text-fg-subtle">Nothing saved yet. Saved scenarios stay in this browser only.</p>;
  return (
    <ul className="space-y-2">
      {items.map((s) => (
        <li key={s.id} className="rounded-lg border border-line p-3 text-xs">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate font-medium text-fg">{s.name}</p>
              <p className="mt-0.5 text-fg-subtle">
                {s.request.country} · {s.request.horizon}Q · as of {s.request.as_of ?? "latest"} · {describeShocks(s.request.shocks ?? {}, spec)}
              </p>
              <p className="mt-0.5 font-mono text-fg-muted">
                {formatProbability(s.baseline)} → {formatProbability(s.scenario)} · {s.modelId}
              </p>
            </div>
            <div className="flex shrink-0 gap-1">
              <Button size="sm" variant="ghost" onClick={() => onLoad(s)} aria-label={`Load scenario ${s.name}`}>Load</Button>
              <Button size="sm" variant="ghost" onClick={() => onDelete(s.id)} aria-label={`Delete scenario ${s.name}`}>
                <Trash2 aria-hidden />
              </Button>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

function ScenarioBody({ iso2, spec }: { iso2: string; spec: ShockSpec[] }) {
  const { asOf, params, setParam } = useAppContext();
  const horizon = params.get("horizon") === "2" ? "2" : "4";
  const [shocks, setShocks] = useState<Shocks>(() => withinSpec(parseShocks(params.get("s")), spec));
  const settled = useDebouncedValue(shocks, 350);
  const hydrated = useHydrated();
  // Browser-only list; it is rendered only after hydration, so the server never needs it.
  const [saved, setSaved] = useState<SavedScenario[]>(() => (typeof window === "undefined" ? [] : loadSaved()));
  const [name, setName] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  // Keep the URL shareable once a slider position has settled.
  const encoded = serializeShocks(settled, spec);
  useEffect(() => {
    if ((params.get("s") ?? null) !== encoded) setParam("s", encoded);
  }, [encoded, params, setParam]);

  const request = useMemo<ScenarioRequest>(
    () => ({ country: iso2, horizon: Number(horizon), as_of: asOf, shocks: toRequestShocks(withinSpec(settled, spec)) }),
    [iso2, horizon, asOf, settled, spec],
  );
  const evaluation = useScenarioEvaluation(request);
  const r = evaluation.data;
  const answer = evaluation.error instanceof ApiError && [404, 422, 503].includes(evaluation.error.status) ? evaluation.error : null;
  const updating = evaluation.isFetching || settled !== shocks;

  function save() {
    if (!r) return;
    const item = toSaved(r, request, name.trim() || `${iso2} · ${horizon}Q · ${describeShocks(request.shocks ?? {}, spec)}`);
    const next = [item, ...saved];
    setSaved(next);
    setNotice(storeSaved(next) ? "Saved in this browser." : "Could not save: browser storage is unavailable.");
    setName("");
  }

  function remove(id: string) {
    const next = saved.filter((s) => s.id !== id);
    setSaved(next);
    storeSaved(next);
  }

  function load(s: SavedScenario) {
    setShocks(withinSpec(s.request.shocks ?? {}, spec));
    setParam("horizon", String(s.request.horizon));
    setNotice(s.request.country !== iso2 || (s.request.as_of ?? null) !== asOf
      ? `Loaded the shocks of “${s.name}”; it was saved for ${s.request.country}, as of ${s.request.as_of ?? "latest"}.`
      : `Loaded “${s.name}”.`);
  }

  function exportJson() {
    if (!r) return;
    downloadText(`macropulse-scenario-${iso2.toLowerCase()}-h${horizon}-${r.as_of}.json`, scenarioExport(r, request), "application/json");
  }

  return (
    <div className="grid gap-4 xl:grid-cols-5">
      <div className="space-y-4 xl:col-span-2">
        <Card>
          <CardHeader title="Shocks" description="Added to the latest published model inputs, then re-scored by the published model." />
          <CardBody className="space-y-5">
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-subtle">Horizon</p>
              <Segmented label="Recession horizon" options={HORIZONS} value={horizon} onChange={(v) => setParam("horizon", v)} />
            </div>
            {spec.map((s) => (
              <ShockSlider key={s.key} spec={s} value={shocks[s.key] ?? 0} onChange={(v) => setShocks((prev) => ({ ...prev, [s.key]: v }))} />
            ))}
            <div className="flex flex-wrap gap-2 border-t border-line pt-4">
              <Button size="sm" onClick={() => setShocks({})} disabled={isUnshocked(shocks)}>
                <RotateCcw aria-hidden />
                Reset
              </Button>
              <Button size="sm" onClick={exportJson} disabled={!r || updating}>
                <FileDown aria-hidden />
                Export JSON
              </Button>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Saved scenarios" description="Stored in this browser (localStorage); nothing is sent to the server." />
          <CardBody className="space-y-3">
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                save();
              }}
            >
              <label htmlFor="scenario-name" className="sr-only">Scenario name</label>
              <input
                id="scenario-name"
                value={name}
                maxLength={80}
                onChange={(e) => setName(e.target.value)}
                placeholder="Name (optional)"
                className="h-8 min-w-0 flex-1 rounded-lg border border-line-strong bg-surface-2 px-3 text-sm text-fg placeholder:text-fg-subtle"
              />
              <Button size="sm" type="submit" disabled={!r || updating}>
                <Save aria-hidden />
                Save
              </Button>
            </form>
            {notice ? <p role="status" className="text-xs text-fg-muted">{notice}</p> : null}
            {hydrated ? <SavedList items={saved} spec={spec} onLoad={load} onDelete={remove} /> : null}
          </CardBody>
        </Card>
      </div>

      <div className="min-w-0 space-y-4 xl:col-span-3">
        {evaluation.isPending ? (
          <Skeleton className="h-[420px] rounded-card" />
        ) : answer ? (
          <EmptyState icon={<SlidersHorizontal className="size-6" aria-hidden />} title={answer.status === 503 ? "Model not available" : "No scenario for this selection"}>
            {answer.message}
          </EmptyState>
        ) : evaluation.error || !r ? (
          <ErrorState error={evaluation.error} onRetry={() => void evaluation.refetch()} />
        ) : (
          <>
            <ResultCard r={r} updating={updating} />
            <Card>
              <CardHeader
                title="What moved the probability"
                description={`Change in each input's contribution (${r.explanation_unit}), largest first.`}
              />
              <CardBody>
                <DeltaList items={r.contributions} unit={r.explanation_unit} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader title="Model inputs" description="Baseline values come from published data at the as-of; shocked inputs are highlighted." />
              <CardBody>
                <InputsTable r={r} />
              </CardBody>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

export function ScenariosView() {
  const { country, asOf } = useAppContext();
  const countries = useCountries();
  const spec = useScenarioSpec();
  const selected = countries.data?.items.find((c) => c.iso2 === country);

  return (
    <>
      <PageHeader
        eyebrow="Models"
        title="Scenario lab"
        description="Shift the published recession model's inputs within bounded ranges and see how its probability responds."
        meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
      />
      <div role="note" className="mb-4 rounded-xl border border-warn/40 bg-warn/[0.08] px-4 py-3 text-sm text-fg">
        <p className="font-medium">{spec.data?.disclaimer ?? FALLBACK_DISCLAIMER}</p>
        <p className="mt-1 text-fg-muted">
          Shocks move model inputs mechanically; nothing here models how the economy would react. The output shows how this
          particular model responds, including where it extrapolates beyond its training data.
        </p>
      </div>
      {!selected ? (
        <CountryRequired purpose="Scenarios start from one country's latest published inputs." />
      ) : spec.isPending ? (
        <Skeleton className="h-[520px] rounded-card" />
      ) : spec.error || !spec.data ? (
        <ErrorState error={spec.error} onRetry={() => void spec.refetch()} />
      ) : (
        <ScenarioBody key={`${selected.iso2}-${asOf ?? "latest"}`} iso2={selected.iso2} spec={spec.data.shocks} />
      )}
    </>
  );
}
