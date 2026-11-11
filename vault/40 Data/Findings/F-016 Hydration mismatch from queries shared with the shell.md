---
type: finding
id: F-016
severity: low
status: resolved
area: web
found: 2026-11-11
tags:
  - finding
---

# F-016 · Hydration mismatch from queries shared with the shell

> [!finding] Low severity · resolved
> In the development server the overview logged "Hydration failed because the server rendered HTML didn't match the client" for `SourceRegistry`: the server HTML had the loading skeleton, the first client render already had the table.

## Evidence (2026-11-11, `pnpm dev`, `/?country=DE`)
- React's diff: server `aria-label="Loading sources"` skeleton vs client `role="region"` table inside `OverviewView`'s Suspense boundary.
- Cause: `useSourcesStatus` is also used by the top bar (`SyncStatus`). The shell hydrates first and starts the request; with slow (development) hydration the response arrives before the page's Suspense boundary hydrates, so that boundary's first client render sees data the server never had. The production build hydrates fast enough that the 58 Playwright tests never hit it, but a slow device could.
- Same race possible for `useCountries` (country switcher ↔ page title, country grid), `useHealth` and `useReady`.

## Resolution
`usePendingUntilHydrated` in `apps/web/src/lib/queries.ts` reports those four shell-shared queries as pending until hydration has completed (`useHydrated`), exactly as the server rendered them. After the change, reloading the overview for two countries added no new hydration error to the console.

Related: [[Phase 10 — Hardening & release]] · [[ADR-0023 Opaque panels, shared chart theme and decorative motion]]
