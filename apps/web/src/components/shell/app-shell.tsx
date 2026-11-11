"use client";

import { usePathname } from "next/navigation";
import { type ReactNode, Suspense, useState } from "react";

import { DemoBanner } from "@/components/shell/demo-banner";
import { MobileNav } from "@/components/shell/mobile-nav";
import { Sidebar } from "@/components/shell/sidebar";
import { Topbar } from "@/components/shell/topbar";
import { useHealth } from "@/lib/queries";

function Footer() {
  const { data } = useHealth();
  return (
    <footer className="relative px-4 py-5 text-xs text-fg-subtle sm:px-6 lg:px-8">
      <span aria-hidden className="hairline absolute inset-x-0 top-0 h-px" />
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
  return <div className="sticky top-0 z-30 h-14 bg-canvas/70" aria-hidden />;
}

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[256px_minmax(0,1fr)]">
      <a
        href="#main"
        className="sr-only z-50 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-canvas focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
      >
        Skip to content
      </a>
      <aside className="sticky top-0 z-10 hidden h-dvh border-r border-line bg-[linear-gradient(180deg,#10182b_0%,#0c1222_55%,#0b1020_100%)] lg:block">
        <Suspense fallback={null}>
          <Sidebar />
        </Suspense>
      </aside>
      <Suspense fallback={null}>
        <MobileNav open={menuOpen} onOpenChange={setMenuOpen} />
      </Suspense>

      <div className="relative flex min-w-0 flex-col">
        <div aria-hidden className="aurora" />
        <Suspense fallback={<TopbarFallback />}>
          <Topbar onOpenMenu={() => setMenuOpen(true)} />
        </Suspense>
        <DemoBanner />
        <main id="main" tabIndex={-1} className="relative z-[1] flex-1 px-4 py-6 focus:outline-none sm:px-6 sm:py-8 lg:px-8">
          {/* keyed by route: the content rises in once per page, not on every filter change */}
          <div key={pathname} className="page-enter mx-auto w-full max-w-7xl">
            {children}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}
