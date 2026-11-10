import { useSyncExternalStore } from "react";

const subscribe = () => () => {};

/**
 * False during server rendering and hydration, true afterwards. Components whose first client
 * render could see data the server did not have (a query that resolved while a sibling boundary
 * was still hydrating) render their server state until hydration completes.
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(subscribe, () => true, () => false);
}
