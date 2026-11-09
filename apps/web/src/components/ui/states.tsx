"use client";

import { CircleExclamationPoint, Info, RefreshCw, ServerOff } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/cn";

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  className?: string;
}

/** Structured error with a working retry. Shows the API error code and request id for support. */
export function ErrorState({ error, onRetry, title, className }: ErrorStateProps) {
  const apiError = error instanceof ApiError ? error : null;
  const unreachable = apiError?.isUnreachable ?? false;
  const Icon = unreachable ? ServerOff : CircleExclamationPoint;
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-start gap-3 rounded-xl border border-danger/25 bg-danger/5 p-4 text-sm",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 size-4 shrink-0 text-danger" aria-hidden />
        <div className="min-w-0">
          <p className="font-medium text-fg">{title ?? (unreachable ? "API unreachable" : "Request failed")}</p>
          <p className="mt-1 text-fg-muted">{apiError?.message ?? "Something went wrong."}</p>
          {apiError ? (
            <p className="mt-1 font-mono text-[11px] text-fg-subtle">
              {apiError.code}
              {apiError.status ? ` · HTTP ${apiError.status}` : ""}
              {apiError.requestId ? ` · request ${apiError.requestId}` : ""}
            </p>
          ) : null}
        </div>
      </div>
      {onRetry ? (
        <Button size="sm" onClick={onRetry}>
          <RefreshCw aria-hidden />
          Retry
        </Button>
      ) : null}
    </div>
  );
}

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, children, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 rounded-xl border border-dashed border-line-strong bg-surface-2/40 px-6 py-10 text-center",
        className,
      )}
    >
      <div className="text-fg-subtle">{icon ?? <Info className="size-5" aria-hidden />}</div>
      <p className="text-sm font-medium text-fg">{title}</p>
      {children ? <div className="max-w-md text-sm text-fg-muted">{children}</div> : null}
      {action}
    </div>
  );
}

export function Notice({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border border-accent/25 bg-accent/[0.06] px-4 py-3 text-sm text-fg-muted",
        className,
      )}
    >
      <Info className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
