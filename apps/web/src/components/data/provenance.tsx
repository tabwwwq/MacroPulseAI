import type { SeriesProvenance } from "@macropulse/shared-types";

import { formatDateTimeUtc } from "@/lib/format";

/** Compact definition list of where a value comes from. Used in KPI tooltips and chart notes. */
export function ProvenanceDetails({
  provenance: p,
  transform,
  period,
  flag,
}: {
  provenance: SeriesProvenance;
  transform?: string | null;
  period?: string | null;
  flag?: string | null;
}) {
  const rows: [string, string][] = [
    ["Source", p.source_name],
    ["Dataset", `${p.dataset} · ${p.series_key}`],
    ...(period ? ([["Period", flag ? `${period} (${flag})` : period]] as [string, string][]) : []),
    ...(transform ? ([["Derivation", transform]] as [string, string][]) : []),
    ["Native unit", p.adjustment ? `${p.native_unit} · ${p.adjustment}` : p.native_unit],
    ["Stored", `${p.native_observations} observations`],
    ["Retrieved", formatDateTimeUtc(p.retrieved_at)],
    ["Source updated", p.source_updated_at ?? "not reported"],
  ];
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="text-fg-subtle">{k}</dt>
          <dd className="min-w-0 break-words text-fg">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
