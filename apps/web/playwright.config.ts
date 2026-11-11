import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests against the real stack: FastAPI on :8000 and the Next.js server on :3000.
 *
 * Locally the servers are reused when they are already running (`pnpm dev`, or `pnpm start` after a
 * production build); otherwise Playwright starts them. Locally the installed Chrome is used (no
 * browser download); CI installs Chromium. The data-dependent flows need stored data and a trained
 * model: run `uv run macropulse demo-load` and `uv run macropulse train` (or a live sync) first.
 */
const CI = Boolean(process.env.CI);
const BASE_URL = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1, // one API process with SQLite; keep requests sequential and rate limits predictable
  retries: CI ? 1 : 0,
  reporter: CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...(CI ? {} : { channel: "chrome" }),
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"], viewport: { width: 375, height: 812 } },
      testIgnore: /flows\.spec\.ts/, // the full flows run once, on desktop
    },
  ],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : [
        {
          command: "uv run macropulse serve --host 127.0.0.1 --port 8000",
          cwd: "../..",
          url: "http://127.0.0.1:8000/api/health",
          reuseExistingServer: !CI,
          timeout: 120_000,
        },
        {
          command: CI ? "pnpm start --hostname 127.0.0.1 --port 3000" : "pnpm dev --hostname 127.0.0.1 --port 3000",
          url: BASE_URL,
          reuseExistingServer: !CI,
          timeout: 180_000,
        },
      ],
});
