"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/shell/logo";
import { cn } from "@/lib/cn";
import { useAppContext } from "@/lib/context";
import { CURRENT_PHASE, MODULE_GROUPS, MODULES, moduleForPath } from "@/lib/modules";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const active = moduleForPath(pathname);
  const { hrefWithContext } = useAppContext();

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center px-5">
        <Logo onNavigate={onNavigate} />
      </div>

      <nav aria-label="Primary" className="flex-1 overflow-y-auto px-3 pb-4 pt-2">
        {MODULE_GROUPS.map((group) => (
          <div key={group} className="mb-5">
            <p className="px-3 pb-1.5 font-mono text-[10.5px] font-medium uppercase tracking-[0.14em] text-fg-subtle">
              {group}
            </p>
            <ul className="space-y-0.5">
              {MODULES.filter((m) => m.group === group).map((m) => {
                const isActive = active?.id === m.id;
                const Icon = m.icon;
                return (
                  <li key={m.id}>
                    <Link
                      href={hrefWithContext(m.href)}
                      onClick={onNavigate}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200",
                        isActive
                          ? "bg-gradient-to-r from-accent/[0.16] via-accent/[0.06] to-transparent font-medium text-fg shadow-[inset_0_0_0_1px_rgb(76_195_255/0.14)]"
                          : "text-fg-muted hover:translate-x-0.5 hover:bg-surface-2/70 hover:text-fg",
                      )}
                    >
                      {isActive ? (
                        <span
                          aria-hidden
                          className="absolute inset-y-1.5 left-0 w-[3px] rounded-full bg-accent shadow-[0_0_12px_1px_rgb(76_195_255/0.8)]"
                        />
                      ) : null}
                      <Icon
                        aria-hidden
                        className={cn(
                          "size-4 shrink-0 transition-colors",
                          isActive ? "text-accent drop-shadow-[0_0_6px_rgb(76_195_255/0.7)]" : "text-fg-subtle group-hover:text-accent",
                        )}
                      />
                      <span className="truncate">{m.label}</span>
                      {m.state === "planned" ? (
                        <span
                          className="ml-auto font-mono text-[10px] text-fg-subtle"
                          title={`Scheduled for phase ${m.phase}`}
                        >
                          P{m.phase}
                        </span>
                      ) : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="m-3 rounded-xl border border-line bg-surface/70 px-4 py-3.5 shadow-[inset_0_1px_0_rgb(255_255_255/0.04)]">
        <p className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-fg-subtle">Build status</p>
        <p className="mt-1 text-xs text-fg-muted">
          Phase {CURRENT_PHASE.number} of {CURRENT_PHASE.total} · {CURRENT_PHASE.name}
        </p>
        <div
          className="mt-2.5 h-1.5 rounded-full bg-canvas"
          role="progressbar"
          aria-label="Build progress"
          aria-valuemin={0}
          aria-valuemax={CURRENT_PHASE.total}
          aria-valuenow={CURRENT_PHASE.number}
        >
          <div
            className="h-full rounded-full bg-gradient-to-r from-iris via-accent to-ok shadow-[0_0_10px_rgb(76_195_255/0.7)]"
            style={{ width: `${(CURRENT_PHASE.number / CURRENT_PHASE.total) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
