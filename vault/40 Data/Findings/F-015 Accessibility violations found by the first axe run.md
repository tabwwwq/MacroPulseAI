---
type: finding
id: F-015
severity: medium
status: resolved
area: web
found: 2026-11-11
tags:
  - finding
---

# F-015 · Accessibility violations found by the first axe run

> [!finding] Medium severity · resolved
> The first Playwright run with axe-core (WCAG 2.0/2.1 A and AA) against the production build failed 26 of 58 tests. Earlier manual browser checks had not caught these problems.

## Evidence (first run, 2026-11-11)
- `color-contrast` (serious): primary buttons, white on `#2f9bff` ≈ 2.9:1 (history, reports, presets); subtle count text on the highlighted diagnostics row.
- `scrollable-region-focusable` (serious): eleven horizontally scrollable tables could not be reached with the keyboard (compare, recession, forecasts, scenarios, history, lab, data observatory, country explorer).
- `link-in-text-block` (serious): the ML-laboratory link inside a sentence on the recession page was distinguished by colour only.
- Console: `Failed to load resource: 404` on every page — the app had no favicon.
- One test targeted the wrong country tab (no charts on the overview tab); fixed in the test.

## Resolution
Primary actions use dark text on the bright accent (≈ 9:1); the subtle text token went from `#7f8aa3` to `#8a95ad`; scroll containers are focusable labelled regions; in-text links are underlined; `app/icon.svg` added. Result: 58/58, no serious or critical violations on any page at 1440 px or 375 px. The suite now runs in CI.

Related: [[Phase 10 — Hardening & release]]
