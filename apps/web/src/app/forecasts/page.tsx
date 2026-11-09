import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/data/module-placeholder";

export const metadata: Metadata = { title: "Forecast studio" };

export default function ForecastsPage() {
  return <ModulePlaceholder moduleId="forecasts" />;
}
