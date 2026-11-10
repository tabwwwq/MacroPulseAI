import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { LabView } from "@/components/views/lab-view";

export const metadata: Metadata = { title: "ML laboratory" };

export default function LabPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <LabView />
    </Suspense>
  );
}
