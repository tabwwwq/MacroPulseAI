import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-line-strong bg-surface-2 text-fg-muted",
        accent: "border-accent/30 bg-accent/10 text-accent",
        ok: "border-ok/30 bg-ok/10 text-ok",
        warn: "border-warn/30 bg-warn/10 text-warn",
        danger: "border-danger/30 bg-danger/10 text-danger",
      },
      dashed: { true: "border-dashed", false: "" },
    },
    defaultVariants: { tone: "neutral", dashed: false },
  },
);

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, tone, dashed, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone, dashed }), className)} {...props} />;
}

const dotTone = {
  neutral: "bg-fg-subtle",
  accent: "bg-accent",
  ok: "bg-ok",
  warn: "bg-warn",
  danger: "bg-danger",
} as const;

export function StatusDot({ tone, pulse = false }: { tone: keyof typeof dotTone; pulse?: boolean }) {
  return (
    <span aria-hidden className="relative inline-flex size-2">
      {pulse ? (
        <span className={cn("absolute inset-0 animate-ping rounded-full opacity-60", dotTone[tone])} />
      ) : null}
      <span className={cn("relative inline-flex size-2 rounded-full", dotTone[tone])} />
    </span>
  );
}
