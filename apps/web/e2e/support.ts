import { expect, type Page } from "@playwright/test";

/** Every page of the app, with a country selected where the page needs one. */
export const ROUTES = [
  "/?country=DE",
  "/countries",
  "/countries/de",
  "/compare?country=DE",
  "/recession?country=DE",
  "/forecasts?country=DE",
  "/scenarios?country=DE",
  "/history?country=DE",
  "/lab",
  "/data",
  "/reports?country=DE",
] as const;

const BENIGN = [
  /Download the React DevTools/,
  /\[HMR\]|\[Fast Refresh\]/, // dev server only
];

/** Collects console errors and uncaught page errors (the test asserts the list is empty). */
export function watchConsole(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error" && !BENIGN.some((re) => re.test(msg.text()))) errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  return errors;
}

/** Wait until the page has rendered its heading and pending requests settled. */
export async function settle(page: Page): Promise<void> {
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.waitForLoadState("networkidle");
}

export async function horizontalOverflow(page: Page): Promise<number> {
  return page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
}

/** True when the API has stored data and a published model (needed by the full flows). */
export async function hasDataAndModel(page: Page): Promise<boolean> {
  const sources = await page.request.get("/api/sources/status");
  const models = await page.request.get("/api/models?run=latest");
  if (!sources.ok() || !models.ok()) return false;
  const synced = ((await sources.json()) as { items: { last_success_at: string | null }[] }).items.some(
    (s) => s.last_success_at,
  );
  const trained = ((await models.json()) as { items: unknown[] }).items.length > 0;
  return synced && trained;
}
