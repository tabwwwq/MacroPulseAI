import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { ForecastsView } from "@/components/views/forecasts-view";

export const metadata: Metadata = { title: "Forecast studio" };

export default function ForecastsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <ForecastsView />
    </Suspense>
  );
}
