import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/data/module-placeholder";

export const metadata: Metadata = { title: "Scenario lab" };

export default function ScenariosPage() {
  return <ModulePlaceholder moduleId="scenarios" />;
}
