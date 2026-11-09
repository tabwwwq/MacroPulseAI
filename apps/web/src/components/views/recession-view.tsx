"use client";

import { Gauge } from "lucide-react";

import { ChartFrame } from "@/components/charts/chart-frame";
import { CountryRequired } from "@/components/views/country-required";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { WidgetBoundary } from "@/components/ui/error-boundary";
import { PageHeader } from "@/components/ui/page-header";
import { Segmented } from "@/components/ui/segmented";
import { EmptyState } from "@/components/ui/states";
import { formatAsOf } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";
import { useCountries } from "@/lib/queries";

type Horizon = "2" | "4";

export function RecessionView() {
  const { country, asOf, params, setParam } = useAppContext();
  const countries = useCountries();
  const selected = countries.data?.items.find((c) => c.iso2 === country);
  const horizon: Horizon = params.get("h") === "4" ? "4" : "2";

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
              value={horizon}
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
      ) : (
        <div className="grid gap-4 xl:grid-cols-3">
          <Card>
            <CardHeader title={`Probability · next ${horizon} quarters`} description={`${selected.name} · as of ${formatAsOf(asOf)}`} />
            <CardBody>
              <EmptyState icon={<Gauge className="size-6" aria-hidden />} title="Model not trained">
                No model artifact exists yet, so no probability is shown. The first models (prevalence baseline,
                logistic regression, gradient boosting) are trained and backtested in Phase 5; this card will then show
                the calibrated probability with model version, training cut-off and data freshness.
              </EmptyState>
            </CardBody>
          </Card>
          <div className="min-w-0 xl:col-span-2">
            <WidgetBoundary label="Risk trend">
              <ChartFrame
                title={`Risk trend · H=${horizon}`}
                description="Out-of-sample probabilities from walk-forward backtests, with realised technical recessions shaded."
                series={[]}
                emptyTitle="No backtested probabilities yet"
                emptyMessage="Historic probabilities come only from genuine walk-forward evaluation — never from a model fitted on the future."
                exportName={`macropulse-${selected.iso2.toLowerCase()}-risk-h${horizon}`}
                height={260}
              />
            </WidgetBoundary>
          </div>

          <Card>
            <CardHeader title="Event definition" />
            <CardBody className="space-y-2 text-sm leading-relaxed text-fg-muted">
              <p>
                At the as-of quarter <span className="font-mono text-fg">t</span>, the event is <span className="text-fg">1</span> if at
                least one pair of consecutive quarters with negative q/q real-GDP growth lies entirely inside{" "}
                <span className="font-mono text-fg">t+1 … t+{horizon}</span>.
              </p>
              <p>Zero growth is not negative. Quarters whose horizon is not yet observed are censored.</p>
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Why this probability?" />
            <CardBody className="text-sm leading-relaxed text-fg-muted">
              Feature contributions (SHAP, or standardised coefficients / permutation importance as a documented fallback)
              appear here for each estimate once a model exists.
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Limitations" />
            <CardBody>
              <ul className="list-disc space-y-1.5 pl-4 text-sm text-fg-muted">
                <li>Few technical recessions per country → wide uncertainty; metrics are reported with sample and event counts.</li>
                <li>Eurostat serves revised data; historic views are a revised-data / release-lag approximation.</li>
                {selected.iso2 === "US" ? (
                  <li>NBER recession dates are an external reference only, not the training target.</li>
                ) : (
                  <li>The policy rate is the shared ECB rate for all euro area members.</li>
                )}
              </ul>
            </CardBody>
          </Card>
        </div>
      )}
    </>
  );
}
