"use client";

import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";

import { CountrySwitcher } from "@/components/shell/country-switcher";
import { LogoMark } from "@/components/shell/logo";
import { SyncStatus } from "@/components/shell/sync-status";
import { moduleForPath } from "@/lib/modules";

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const current = moduleForPath(usePathname());

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-canvas/80 px-4 backdrop-blur-md sm:px-6 lg:px-8">
      <button
        type="button"
        onClick={onOpenMenu}
        aria-label="Open navigation"
        className="inline-flex size-9 items-center justify-center rounded-lg text-fg-muted hover:bg-surface-2 hover:text-fg lg:hidden"
      >
        <Menu className="size-5" aria-hidden />
      </button>
      <LogoMark className="hidden size-7 sm:block lg:hidden" />

      {current ? (
        <p className="hidden min-w-0 truncate text-sm text-fg-muted sm:block" aria-label="Breadcrumb">
          <span className="text-fg-subtle">{current.group}</span>
          <span className="mx-2 text-line-strong" aria-hidden>
            /
          </span>
          <span className="text-fg">{current.label}</span>
        </p>
      ) : null}

      <div className="ml-auto flex min-w-0 items-center gap-2">
        <CountrySwitcher />
        <SyncStatus />
      </div>
    </header>
  );
}
