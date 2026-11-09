"use client";

import { ErrorState } from "@/components/ui/states";

export default function RouteError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <ErrorState className="mt-10" title="This page failed to render" error={error} onRetry={reset} />;
}
