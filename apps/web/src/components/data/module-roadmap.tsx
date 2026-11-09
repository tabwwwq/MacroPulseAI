import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { MODULES } from "@/lib/modules";

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
              <Badge tone={m.state === "foundation" ? "accent" : "neutral"} dashed={m.state === "planned"}>
                {m.state === "foundation" ? "Foundation" : "Planned"} · P{m.phase}
              </Badge>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
