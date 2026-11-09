import type { Metadata } from "next";

import { CountryGrid } from "@/components/data/country-grid";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Countries" };

export default function CountriesPage() {
  return (
    <>
      <PageHeader
        eyebrow="Monitor"
        title="Countries"
        description="Initial fully targeted economies. Further countries (UK, Italy, Spain, Poland, Romania, euro area) are added only after their GDP target and indicators are mapped and validated."
      />
      <CountryGrid />
    </>
  );
}
