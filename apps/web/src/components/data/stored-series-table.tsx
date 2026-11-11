"use client";

import { Download, ExternalLink } from "lucide-react";

import type { StoredSeries } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";
import { formatDateTimeUtc } from "@/lib/format";

const HEALTH = {
  pass: { tone: "ok", label: "Checks pass" },
  warn: { tone: "warn", label: "Warnings" },
  fail: { tone: "danger", label: "Last sync failed" },
  not_synced: { tone: "neutral", label: "Not synced" },
} as const;

export function publisherOf(s: Pick<StoredSeries, "source_id" | "source_name">): string {
  if (s.source_id === "fred") return "FRED";
  if (s.source_id === "ecb") return "ECB";
  return s.source_name.split(" ")[0] ?? s.source_id;
}

/**
 * Lineage of stored native series: what was requested, how much is stored, when it was fetched and
 * the latest quality checks, with the raw rows downloadable for independent verification.
 */
export function StoredSeriesTable({ items, showGeo = false }: { items: StoredSeries[]; showGeo?: boolean }) {
  return (
    <div className="relative -mx-5 overflow-x-auto px-5 focus-visible:outline-2 focus-visible:outline-accent" tabIndex={0} role="region" aria-label="Table, scrolls horizontally">
      <table className="w-full min-w-[920px] text-left text-sm">
        <caption className="sr-only">Stored official series, lineage and quality</caption>
        <thead>
          <tr className="border-b border-line text-xs text-fg-subtle">
            <th scope="col" className="py-2 pr-4 font-medium">Series</th>
            {showGeo ? <th scope="col" className="py-2 pr-4 font-medium">Geo</th> : null}
            <th scope="col" className="py-2 pr-4 font-medium">Stored</th>
            <th scope="col" className="py-2 pr-4 font-medium">Span</th>
            <th scope="col" className="py-2 pr-4 font-medium">Fetched</th>
            <th scope="col" className="py-2 pr-4 font-medium">Latest checks</th>
            <th scope="col" className="py-2 font-medium">Raw data</th>
          </tr>
        </thead>
        <tbody>
          {items.map((s) => {
            const health = HEALTH[s.health];
            const problems = s.quality.filter((q) => q.status !== "pass");
            return (
              <tr key={s.series_id} className="border-b border-line/60 align-top last:border-0">
                <th scope="row" className="max-w-[22rem] py-3 pr-4 font-normal">
                  <p className="font-medium text-fg">
                    {publisherOf(s)} · <span className="font-mono">{s.dataset}</span>
                  </p>
                  <p className="break-words font-mono text-[11px] text-fg-subtle">{s.series_key}</p>
                  <p className="mt-1 text-xs text-fg-muted">
                    {s.unit} · {s.frequency}
                    {s.adjustment ? ` · ${s.adjustment}` : ""} → {s.indicators.join(", ")}
                    {s.countries.length > 1 ? ` · shared by ${s.countries.join(", ")}` : ""}
                  </p>
                </th>
                {showGeo ? <td className="py-3 pr-4 font-mono text-xs text-fg">{s.geo}</td> : null}
                <td className="tabular py-3 pr-4 font-mono text-xs text-fg">{s.observations.toLocaleString("en")}</td>
                <td className="tabular whitespace-nowrap py-3 pr-4 font-mono text-xs text-fg-muted">
                  {s.first_period ? `${s.first_period} → ${s.last_period}` : "—"}
                </td>
                <td className="py-3 pr-4 text-xs text-fg-muted">
                  {formatDateTimeUtc(s.retrieved_at)}
                  {s.source_updated_at ? <p className="text-fg-subtle">source updated {s.source_updated_at}</p> : null}
                </td>
                <td className="max-w-[20rem] py-3 pr-4 text-xs">
                  <Badge tone={health.tone} dashed={s.health === "not_synced"}>
                    {health.label}
                  </Badge>
                  {s.quality.length ? (
                    <details className="mt-1.5 text-fg-muted">
                      <summary className="cursor-pointer text-fg-subtle hover:text-fg">
                        {s.quality.length} check{s.quality.length === 1 ? "" : "s"}
                        {problems.length ? ` · ${problems.length} to review` : ""}
                        {s.last_checked_run_id ? ` · run ${s.last_checked_run_id}` : ""}
                      </summary>
                      <ul className="mt-1 space-y-1">
                        {s.quality.map((q) => (
                          <li
                            key={q.rule}
                            className={q.status === "fail" ? "text-danger" : q.status === "warn" ? "text-warn" : undefined}
                          >
                            <span className="font-mono">{q.status}</span> · {q.rule.replaceAll("_", " ")}: {q.detail}
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </td>
                <td className="py-3 text-xs">
                  <div className="flex flex-col items-start gap-1.5">
                    {s.observations > 0 ? (
                      <a href={s.export_path} download className="inline-flex items-center gap-1 text-accent hover:underline">
                        <Download className="size-3" aria-hidden />
                        CSV
                        <span className="sr-only">
                          {" "}
                          of {s.dataset} {s.geo} raw observations
                        </span>
                      </a>
                    ) : null}
                    {s.request_url ? (
                      <a
                        href={s.request_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-fg-muted hover:text-accent"
                      >
                        <ExternalLink className="size-3" aria-hidden />
                        Request
                        <span className="sr-only"> (official API, opens in a new tab)</span>
                      </a>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
