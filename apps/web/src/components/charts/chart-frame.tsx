"use client";

import { useId, useRef, useState, type JSX, type ReactNode } from "react";

import { DataTable } from "@/components/charts/data-table";
import { TimeSeriesChart, type TimeSeriesChartHandle } from "@/components/charts/time-series-chart";
import type { ChartKind, ChartSeries, ChartShading, ChartSource } from "@/components/charts/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { cn } from "@/lib/cn";
import { downloadDataUrl, downloadText, seriesToCsv } from "@/lib/export";
import { formatDateTimeUtc } from "@/lib/format";

export interface ChartFrameProps {
  title: string;
  description?: ReactNode;
  series: ChartSeries[];
  isLoading?: boolean;
  error?: unknown;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyMessage?: ReactNode;
  source?: ChartSource;
  staleSince?: string | null;
  allowKindToggle?: boolean;
  defaultKind?: ChartKind;
  shading?: ChartShading[];
  height?: number;
  exportName: string;
}

export function ChartFrame({
  title, description, series, isLoading = false, error, onRetry,
  emptyTitle = "No observations yet", emptyMessage, source, staleSince,
  allowKindToggle = false, defaultKind = "line", shading, height = 280, exportName,
}: ChartFrameProps): JSX.Element {
  const [kind, setKind] = useState(defaultKind);
  const [tableView, setTableView] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const chart = useRef<TimeSeriesChartHandle>(null);
  const tableId = useId();
  const hasData = series.some(({ points }) => points.some(({ value }) => value !== null && Number.isFinite(value)));
  const hasError = error !== undefined && error !== null;
  const ready = !isLoading && !hasError && hasData;

  function exportFile(format: "csv" | "png") {
    try {
      if (format === "csv") {
        downloadText(`${exportName}.csv`, seriesToCsv(series));
      } else {
        const url = chart.current?.getPngDataUrl();
        if (!url) throw new Error("Chart image unavailable");
        downloadDataUrl(`${exportName}.png`, url);
      }
      setExportError(null);
    } catch {
      setExportError(`${format.toUpperCase()} export failed. Please try again.`);
    }
  }

  return (
    <Card aria-label={title}>
      <CardHeader title={title} description={description} action={ready && staleSince ? <Badge tone="warn">Stale</Badge> : undefined} />
      <CardBody>
        {ready ? (
          <div role="group" aria-label={`${title} chart controls`} className="mb-3 flex flex-wrap items-center gap-2">
            {allowKindToggle ? (
              <div role="group" aria-label="Chart kind" className="inline-flex rounded-lg border border-line p-0.5">
                {(["line", "bar"] as const).map((value) => (
                  <Button key={value} size="sm" variant={kind === value ? "secondary" : "ghost"} aria-pressed={kind === value} onClick={() => setKind(value)}>
                    {value === "line" ? "Line" : "Bar"}
                  </Button>
                ))}
              </div>
            ) : null}
            <Button size="sm" aria-pressed={tableView} aria-expanded={tableView} aria-controls={tableId} onClick={() => setTableView((value) => !value)}>Table</Button>
            <Button size="sm" onClick={() => exportFile("csv")}>CSV</Button>
            <Button size="sm" onClick={() => exportFile("png")}>PNG</Button>
          </div>
        ) : null}
        {isLoading ? (
          <div role="status" aria-label={`Loading ${title}`} style={{ height }} className="flex flex-col justify-between gap-4">
            <span className="sr-only">Loading observations</span>
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="min-h-0 flex-1" />
            <Skeleton className="h-3 w-full" />
          </div>
        ) : hasError ? (
          <ErrorState error={error} onRetry={onRetry} />
        ) : !hasData ? (
          <EmptyState title={emptyTitle}>{emptyMessage ?? "No observations are available for this selection. Missing data is not estimated."}</EmptyState>
        ) : (
          <>
            <div className="relative min-w-0">
              {/* Retain chart dimensions in table view so PNG export remains available. */}
              <div className={cn(tableView && "invisible absolute inset-x-0 top-0")} aria-hidden={tableView || undefined}>
                <TimeSeriesChart ref={chart} series={series} kind={kind} height={height} shading={shading} ariaLabel={title} />
              </div>
              <div id={tableId} hidden={!tableView}>
                {tableView ? <DataTable series={series} caption={title} height={height} /> : null}
              </div>
            </div>
            {staleSince ? <p className="mt-3 text-xs text-warn">Data stale since {formatDateTimeUtc(staleSince)}. Displaying the available observations.</p> : null}
            {exportError ? <p role="alert" className="mt-3 text-sm text-danger">{exportError}</p> : null}
          </>
        )}
        {source ? (
          <footer className="mt-4 border-t border-line pt-3 text-xs text-fg-subtle">
            Source: {source.href ? <a className="text-accent underline underline-offset-2" href={source.href} target="_blank" rel="noopener noreferrer">{source.label}</a> : source.label}
            {source.retrievedAt ? ` · retrieved ${formatDateTimeUtc(source.retrievedAt)}` : " · not retrieved yet"}
          </footer>
        ) : null}
      </CardBody>
    </Card>
  );
}
