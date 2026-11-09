"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";

import { ApiError } from "@/lib/api";

function shouldRetry(failureCount: number, error: unknown): boolean {
  // Client/contract errors (4xx, unsupported country, …) are deterministic: don't retry them.
  if (error instanceof ApiError && !error.isUnreachable && error.status < 500) return false;
  return failureCount < 1;
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: shouldRetry },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <Tooltip.Provider delayDuration={200}>{children}</Tooltip.Provider>
    </QueryClientProvider>
  );
}
