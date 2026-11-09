import type { Metadata } from "next";

import { ModulePlaceholder } from "@/components/data/module-placeholder";

export const metadata: Metadata = { title: "ML laboratory" };

export default function LabPage() {
  return <ModulePlaceholder moduleId="lab" />;
}
