import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { ReportsView } from "@/components/views/reports-view";

export const metadata: Metadata = { title: "Reports" };

export default function ReportsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <ReportsView />
    </Suspense>
  );
}
