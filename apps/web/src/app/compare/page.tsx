import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/data/module-placeholder";

export const metadata: Metadata = { title: "Compare" };

export default function ComparePage() {
  return <ModulePlaceholder moduleId="compare" />;
}
