---
type: decision
id: ADR-0011
date: 2026-11-09
status: accepted
area: product
tags:
  - decision
---

# ADR-0011 · Analysis context lives in the URL

> [!decision] Decision
> The selected country and as-of quarter are URL search parameters (`?country=DE&asOf=2008-Q3`; module options such as `h`, `tab`, `metric`, `countries` too). Navigation links carry them forward; country pages take the country from the path.

## Context
Analysts share views and expect "Germany as of Q3 2008, 4-quarter horizon" to be reproducible. Local state or storage would make links meaningless and break back/forward navigation.

## Consequences
- Every view is a shareable, bookmarkable link; browser history works.
- Invalid or future as-of values fall back to "Latest" (no information sets from the future).
- Components that read the context must sit inside a `<Suspense>` boundary (Next.js `useSearchParams`).
- From Phase 5 the API receives `as_of` explicitly, so the URL is the single source of truth for what the model may know.
