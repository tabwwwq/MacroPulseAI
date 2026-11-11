"use client";

import { Braces, FileText, Sheet } from "lucide-react";
import { useState } from "react";

import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorState, Notice } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { downloadReport, type ReportFormat } from "@/lib/reports";
import { useCountries } from "@/lib/queries";

const REPORT_FORMATS: { format: ReportFormat; label: string; icon: typeof FileText }[] = [
  { format: "pdf", label: "Download PDF", icon: FileText },
  { format: "csv", label: "CSV (chart data)", icon: Sheet },
  { format: "json", label: "JSON", icon: Braces },
];

export function ReportsView() {
  const { country, asOf } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);

  const [busyFormat, setBusyFormat] = useState<ReportFormat | null>(null);
  const [savedFilename, setSavedFilename] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [lastFormat, setLastFormat] = useState<ReportFormat>("pdf");

  async function run(format: ReportFormat) {
    if (!selected) return;
    setBusyFormat(format);
    setLastFormat(format);
    setSavedFilename(null);
    setError(null);
    try {
      const filename = await downloadReport({ country: selected.iso2, asOf, format });
      setSavedFilename(filename);
    } catch (err) {
      setError(err);
    } finally {
      setBusyFormat(null);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Platform"
        title="Report builder"
        description="Download a dated report for the selected country: key indicators, charts, model estimates, forecasts, sources and limitations — built only from stored data."
        meta={<Badge tone="neutral">As of {formatAsOf(asOf)}</Badge>}
      />
      {!selected ? (
        <CountryRequired purpose="Reports are generated per country." />
      ) : (
        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Download"
              description={`${selected.name} · ${asOf ? `as of ${asOf}` : "latest stored data"}`}
            />
            <CardBody className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {REPORT_FORMATS.map(({ format, label, icon: Icon }) => (
                  <Button
                    key={format}
                    variant={format === "pdf" ? "primary" : "secondary"}
                    disabled={busyFormat !== null}
                    onClick={() => void run(format)}
                  >
                    <Icon className="size-4" aria-hidden />
                    {busyFormat === format ? "Generating…" : label}
                  </Button>
                ))}
              </div>
              {savedFilename ? (
                <p role="status" className="text-sm text-fg-muted">
                  Saved {savedFilename}
                </p>
              ) : null}
              {error ? <ErrorState error={error} onRetry={() => void run(lastFormat)} /> : null}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="What the report contains" />
            <CardBody>
              <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-fg-muted">
                <li>Key indicators with source flags and staleness.</li>
                <li>
                  Charts of GDP growth (technical recessions shaded), inflation, unemployment and the
                  policy rate for the last 10 years before the cut-off.
                </li>
                <li>
                  Technical-recession estimates for 2 and 4 quarters with their held-out track record
                  (or why there is none). For a past as-of quarter they are marked as in-sample fits, next
                  to the walk-forward estimate made without that outcome.
                </li>
                <li>
                  Ridge-AR forecasts four quarters ahead with 80 % intervals and measured coverage.
                </li>
                <li>
                  Methodology, limitations, numbered sources with request URLs and retrieval times.
                </li>
                <li>Disclaimer.</li>
              </ul>
            </CardBody>
          </Card>

          <Notice>
            Reports use latest revised data. With an as-of quarter, only periods ending by its cut-off
            are included; publication lags are not applied to the key indicators.
          </Notice>
        </div>
      )}
    </>
  );
}
