import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { MODULES, type ModuleState } from "@/lib/modules";

const STATE: Record<ModuleState, { label: string; tone: "ok" | "accent" | "neutral" }> = {
  built: { label: "Built", tone: "ok" },
  foundation: { label: "Foundation", tone: "accent" },
  planned: { label: "Planned", tone: "neutral" },
};

export function ModuleRoadmap() {
  const modules = [...MODULES].sort((a, b) => a.phase - b.phase);
  return (
    <ol className="divide-y divide-line/60">
      {modules.map((m) => {
        const Icon = m.icon;
        return (
          <li key={m.id}>
            <Link href={m.href} className="group flex items-center gap-3 py-2.5">
              <Icon className="size-4 shrink-0 text-fg-subtle group-hover:text-accent" aria-hidden />
              <span className="min-w-0 flex-1 truncate text-sm text-fg-muted group-hover:text-fg">{m.label}</span>
              <Badge tone={STATE[m.state].tone} dashed={m.state === "planned"}>
                {STATE[m.state].label} · P{m.phase}
              </Badge>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
