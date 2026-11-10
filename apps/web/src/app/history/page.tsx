import type { Metadata } from "next";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { HistoryView } from "@/components/views/history-view";

export const metadata: Metadata = { title: "Crisis time machine" };

export default function HistoryPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-card" />}>
      <HistoryView />
    </Suspense>
  );
}
