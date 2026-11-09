import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/data/module-placeholder";

export const metadata: Metadata = { title: "Crisis time machine" };

export default function HistoryPage() {
  return <ModulePlaceholder moduleId="history" />;
}
