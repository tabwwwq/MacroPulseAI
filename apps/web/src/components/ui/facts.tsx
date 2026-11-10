import { TriangleExclamationPoint } from "lucide-react";
import type { ReactNode } from "react";

/** One label/value row of a definition list (use inside <dl>). */
export function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-line/60 py-1.5 text-xs last:border-0">
      <dt className="shrink-0 text-fg-subtle">{label}</dt>
      <dd className="min-w-0 break-words text-right font-mono text-fg">{children}</dd>
    </div>
  );
}

/** Caveat that changes how a number must be read (amber icon + text, never colour alone). */
export function Warning({ children }: { children: ReactNode }) {
  return (
    <div role="note" className="flex gap-2 rounded-lg border border-warn/30 bg-warn/[0.07] p-3 text-xs leading-relaxed text-fg-muted">
      <TriangleExclamationPoint className="mt-0.5 size-4 shrink-0 text-warn" aria-hidden />
      <div>{children}</div>
    </div>
  );
}
