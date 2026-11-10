"use client";

import { Gauge, TriangleExclamationPoint } from "lucide-react";
import Link from "next/link";

import type { RecessionEstimate } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { useAppContext } from "@/lib/context";
import { useRecessionEstimate } from "@/lib/queries";
import { BANDS, HORIZON_CONFLICT_NOTE, formatProbability, horizonConflict } from "@/lib/risk";

function Row({ horizon, e }: { horizon: 2 | 4; e: RecessionEstimate }) {
  const band = BANDS[e.band] ?? { label: e.band, tone: "neutral" as const };
  return (
    <li className="flex items-center justify-between gap-3 py-2">
      <div>
        <p className="text-sm text-fg">Next {horizon} quarters</p>
        <p className="font-mono text-[11px] text-fg-subtle">
          {e.model.name} · base rate {formatProbability(e.base_rate)}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <span className="tabular font-mono text-xl font-semibold text-fg">{formatProbability(e.probability)}</span>
        <Badge tone={band.tone}>{band.label}</Badge>
      </div>
    </li>
  );
}

/** Compact 2Q/4Q estimate for the overview, with the same caveats as the Recession risk page. */
export function RiskSummaryCard({ iso2 }: { iso2: string }) {
  const { asOf, hrefWithContext } = useAppContext();
  const two = useRecessionEstimate(iso2, 2, asOf);
  const four = useRecessionEstimate(iso2, 4, asOf);
  const error = two.error ?? four.error;
  const failing = [two.data, four.data].some((e) => e?.track_record.beats_baseline_heldout === false);
  const inSample = [two.data, four.data].some((e) => e?.in_sample);
  const conflict = horizonConflict(two.data?.probability, four.data?.probability);

  return (
    <Card>
      <CardHeader
        title="Technical-recession risk"
        description={two.data ? `As of ${two.data.as_of}` : undefined}
        action={
          <Link href={hrefWithContext("/recession")} className="text-xs font-medium text-accent hover:underline">
            Details →
          </Link>
        }
      />
      <CardBody>
        {two.isPending || four.isPending ? (
          error ? null : <Skeleton className="h-28 w-full" />
        ) : null}
        {error ? (
          <EmptyState icon={<Gauge className="size-5" aria-hidden />} title={error instanceof ApiError && error.code === "model_not_trained" ? "No trained model yet" : "No estimate"}>
            {error instanceof ApiError ? error.message : "The estimate could not be loaded."}
          </EmptyState>
        ) : two.data && four.data ? (
          <>
            <ul className="divide-y divide-line/60">
              <Row horizon={2} e={two.data} />
              <Row horizon={4} e={four.data} />
            </ul>
            {failing || inSample || conflict ? (
              <p className="mt-3 flex gap-2 text-xs leading-relaxed text-fg-muted">
                <TriangleExclamationPoint className="mt-0.5 size-3.5 shrink-0 text-warn" aria-hidden />
                <span>
                  {failing ? "These models do not beat the historical base rate on the 2015+ held-out years. " : ""}
                  {inSample ? "This as-of quarter was in the training data, so the numbers are fits, not forecasts. " : ""}
                  {conflict ? HORIZON_CONFLICT_NOTE : ""}
                </span>
              </p>
            ) : null}
          </>
        ) : null}
      </CardBody>
    </Card>
  );
}
