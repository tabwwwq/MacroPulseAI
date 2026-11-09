"use client";

import { CountryGrid } from "@/components/data/country-grid";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { useAppContext } from "@/lib/context";

/** Shown by modules that need a country when none is selected yet. */
export function CountryRequired({ purpose }: { purpose: string }) {
  const { setCountry } = useAppContext();
  return (
    <Card>
      <CardHeader title="Choose a country" description={purpose} />
      <CardBody>
        <CountryGrid onSelect={setCountry} />
      </CardBody>
    </Card>
  );
}
