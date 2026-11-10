import type { Contribution } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";
import { formatSigned } from "@/lib/risk";

const value = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });

/**
 * Diverging bar list of feature contributions: right (amber) raises the estimate, left (blue) lowers
 * it. Each row states the input value, its reference period and whether it is unusual for the
 * training sample — so the explanation can be checked against the data pages.
 */
export function Contributions({ items, unit }: { items: Contribution[]; unit: string }) {
  const max = Math.max(...items.map((i) => Math.abs(i.contribution)), 1e-9);
  return (
    <ul className="space-y-2.5" aria-label="Feature contributions">
      {items.map((i) => {
        const width = `${(Math.abs(i.contribution) / max) * 50}%`;
        const up = i.contribution > 0;
        return (
          <li key={i.feature}>
            <div className="flex items-baseline justify-between gap-3 text-xs">
              <span className="min-w-0 text-fg">{i.label}</span>
              <span className="tabular shrink-0 font-mono text-fg-muted">
                {formatSigned(i.contribution)} <span className="text-fg-subtle">{unit}</span>
              </span>
            </div>
            <div className="relative mt-1 h-2 rounded-full bg-surface-2" aria-hidden>
              <span className="absolute inset-y-0 left-1/2 w-px bg-line-strong" />
              <span
                className="absolute inset-y-0 rounded-full"
                style={{
                  width,
                  left: up ? "50%" : undefined,
                  right: up ? undefined : "50%",
                  background: up ? "#f5b544" : "#4cc3ff",
                }}
              />
            </div>
            <p className="mt-1 flex flex-wrap items-center gap-1.5 font-mono text-[11px] text-fg-subtle">
              value {value.format(i.value)}
              {i.period ? ` · ${i.period}` : ""}
              {i.training_mean !== null && i.training_mean !== undefined ? ` · training mean ${value.format(i.training_mean)}` : ""}
              <span className="sr-only">{up ? ", raises the estimate" : ", lowers the estimate"}</span>
              {i.outside_training_range ? (
                <Badge tone="danger">outside training range</Badge>
              ) : i.unusual ? (
                <Badge tone="warn">unusual (outside 5–95%)</Badge>
              ) : null}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
