import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { CompareView } from "@/components/views/compare-view";

export const metadata: Metadata = { title: "Compare" };

export default function ComparePage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <CompareView />
    </Suspense>
  );
}
