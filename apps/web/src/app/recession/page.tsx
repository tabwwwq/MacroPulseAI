import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { RecessionView } from "@/components/views/recession-view";

export const metadata: Metadata = { title: "Recession risk" };

export default function RecessionPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <RecessionView />
    </Suspense>
  );
}
