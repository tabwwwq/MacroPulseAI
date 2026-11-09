import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/data/module-placeholder";

export const metadata: Metadata = { title: "Recession risk" };

export default function RecessionPage() {
  return <ModulePlaceholder moduleId="recession" />;
}
