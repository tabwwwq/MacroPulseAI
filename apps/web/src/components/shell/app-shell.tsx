"use client";

import { type ReactNode, Suspense, useState } from "react";

import { MobileNav } from "@/components/shell/mobile-nav";
import { Sidebar } from "@/components/shell/sidebar";
import { Topbar } from "@/components/shell/topbar";
import { useHealth } from "@/lib/queries";

function Footer() {
  const { data } = useHealth();
  return (
    <footer className="border-t border-line px-4 py-5 text-xs text-fg-subtle sm:px-6 lg:px-8">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <p>
          Analytical estimates only — not investment advice. Statistics © their publishers (Eurostat, ECB,
          FRED, World Bank, OECD).
        </p>
        <p className="font-mono">
          {data ? `api ${data.version} · ${data.environment}` : "api status unknown"}
        </p>
      </div>
    </footer>
  );
}

function TopbarFallback() {
  return <div className="sticky top-0 z-30 h-14 border-b border-line bg-canvas/80" aria-hidden />;
}

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[256px_minmax(0,1fr)]">
      <a
        href="#main"
        className="sr-only z-50 rounded-lg bg-accent-strong px-3 py-2 text-sm text-white focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
      >
        Skip to content
      </a>
      <aside className="sticky top-0 hidden h-dvh border-r border-line bg-surface/50 lg:block">
        <Suspense fallback={null}>
          <Sidebar />
        </Suspense>
      </aside>
      <Suspense fallback={null}>
        <MobileNav open={menuOpen} onOpenChange={setMenuOpen} />
      </Suspense>

      <div className="app-backdrop flex min-w-0 flex-col">
        <Suspense fallback={<TopbarFallback />}>
          <Topbar onOpenMenu={() => setMenuOpen(true)} />
        </Suspense>
        <main id="main" tabIndex={-1} className="flex-1 px-4 py-6 focus:outline-none sm:px-6 sm:py-8 lg:px-8">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
        <Footer />
      </div>
    </div>
  );
}
