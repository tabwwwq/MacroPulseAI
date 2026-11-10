import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { ScenariosView } from "@/components/views/scenarios-view";

export const metadata: Metadata = { title: "Scenario lab" };

export default function ScenariosPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <ScenariosView />
    </Suspense>
  );
}
