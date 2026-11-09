import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { OverviewView } from "@/components/views/overview-view";

export default function OverviewPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <OverviewView />
    </Suspense>
  );
}
