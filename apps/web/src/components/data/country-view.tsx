"use client";

import { Landmark } from "lucide-react";
import Link from "next/link";

import { SupportBadge } from "@/components/data/support-badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { ApiError } from "@/lib/api";
import { useCountry } from "@/lib/queries";

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-surface-2/50 px-4 py-3">
      <dt className="text-xs text-fg-subtle">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-fg">{children}</dd>
    </div>
  );
}

export function CountryView({ iso2 }: { iso2: string }) {
  const { data, isPending, isError, error, refetch } = useCountry(iso2);

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading country">
        <Skeleton className="mb-3 h-4 w-24" />
        <Skeleton className="mb-8 h-9 w-72" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-16 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    if (error instanceof ApiError && error.code === "unsupported_country") {
      return (
        <EmptyState
          title={`“${iso2.toUpperCase()}” is not a supported country`}
          action={
            <Link href="/countries" className={buttonVariants({ size: "sm" })}>
              See supported countries
            </Link>
          }
        >
          {error.message}
        </EmptyState>
      );
    }
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  const sharedRate = data.policy_rate_scope === "euro_area_shared";

  return (
    <>
      <PageHeader
        eyebrow={`Country profile · ${data.iso2} / ${data.iso3}`}
        title={data.name}
        description={`${data.region} · ${data.currency} · primary real-GDP source: ${data.primary_gdp_source}`}
        meta={<SupportBadge support={data.support} />}
      />

      <dl className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Fact label="ISO codes">
          <span className="font-mono">
            {data.iso2} · {data.iso3}
          </span>
        </Fact>
        <Fact label="Currency">{data.currency}</Fact>
        <Fact label="Euro area member">{data.euro_area_member ? "Yes" : "No"}</Fact>
        <Fact label="Policy rate scope">{sharedRate ? "Shared euro area (ECB)" : "National"}</Fact>
      </dl>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Indicators" description="Growth, prices, labour, monetary, fiscal and data-quality sections." />
          <CardBody>
            <EmptyState title="No observations ingested yet">
              {data.support.reason} The indicator explorer (charts, tables, CSV/PNG export) arrives in Phase 4.
            </EmptyState>
          </CardBody>
        </Card>
        <Card>
          <CardHeader
            title={
              <span className="inline-flex items-center gap-2">
                <Landmark className="size-4 text-fg-subtle" aria-hidden />
                Monetary policy note
              </span>
            }
          />
          <CardBody className="text-sm leading-relaxed text-fg-muted">
            {sharedRate ? (
              <p>
                {data.name} is a euro area member. Its policy rate is the ECB&apos;s shared rate (main refinancing /
                deposit facility), not a national central-bank rate, and will be labelled as shared everywhere.
              </p>
            ) : (
              <p>
                {data.name} sets a national policy rate. For the United States, NBER recession dates (FRED
                <span className="font-mono"> USREC</span>) will be shown only as an external reference — never as
                the GDP-based technical-recession target.
              </p>
            )}
          </CardBody>
        </Card>
      </div>
    </>
  );
}
