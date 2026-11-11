import type { ReactNode } from "react";

import { PulseLine } from "@/components/ui/pulse-line";

interface PageHeaderProps {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  meta?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, meta }: PageHeaderProps) {
  return (
    <div className="relative mb-6 flex flex-col gap-4 sm:mb-8 md:flex-row md:items-end md:justify-between">
      {/* Brand motif: a decorative pulse trace behind the right half of the header. */}
      <PulseLine className="pointer-events-none absolute -top-3 right-0 hidden h-24 w-[44%] opacity-80 [mask-image:linear-gradient(90deg,transparent,#000_35%,#000_85%,transparent)] lg:block" />
      <div className="relative min-w-0 max-w-3xl">
        {eyebrow ? (
          <p className="mb-3 flex items-center gap-2.5 font-mono text-[11px] font-medium uppercase tracking-[0.18em] text-accent">
            <span aria-hidden className="h-px w-6 bg-gradient-to-r from-accent to-transparent" />
            {eyebrow}
          </p>
        ) : null}
        <h1 className="text-headline text-[28px] font-semibold leading-tight tracking-tight sm:text-4xl">{title}</h1>
        {description ? (
          <p className="mt-3 text-sm leading-relaxed text-fg-muted sm:text-[15px]">{description}</p>
        ) : null}
      </div>
      {meta ? <div className="relative flex shrink-0 flex-wrap items-center gap-2">{meta}</div> : null}
    </div>
  );
}
