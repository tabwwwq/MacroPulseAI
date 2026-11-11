import { readFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

import { hasDataAndModel, settle } from "./support";

// Full analyst flows on stored data and a trained model (demo snapshot or live sync).
test.beforeEach(async ({ page }) => {
  test.skip(!(await hasDataAndModel(page)), "needs stored data and a trained model (demo-load + train)");
});

test("forecast studio shows a projection with intervals and the backtest", async ({ page }) => {
  await page.goto("/forecasts?country=DE&metric=real_gdp_qoq&horizon=4");
  await settle(page);
  const projection = page.getByRole("table", { name: /Forecast path/ });
  await expect(projection.getByRole("row")).toHaveCount(5); // header + four quarters
  await expect(page.getByRole("table", { name: /Forecast accuracy/ })).toBeVisible();
});

test("scenario lab re-scores the published model when a slider moves", async ({ page }) => {
  await page.goto("/scenarios?country=DE&horizon=4");
  await settle(page);
  await expect(page.getByText("Exploratory model sensitivity analysis, not a causal economic simulation.").first()).toBeVisible();
  await page.getByRole("slider", { name: "Policy rate" }).fill("2");
  await expect(page).toHaveURL(/s=policy_rate%3A2/);
  await expect(page.getByText(/^[+−-]\d+\.\d pp$/).first()).not.toHaveText("0.0 pp");
});

test("crisis time machine replays a preset quarter", async ({ page }) => {
  await page.goto("/history?country=DE");
  await settle(page);
  await page.getByRole("button", { name: /Global financial crisis/ }).click();
  await expect(page).toHaveURL(/asOf=2008-Q2/);
  await expect(page.getByRole("heading", { name: "What the model said at 2008-Q2" })).toBeVisible();
  await expect(page.getByText(/revised-data \/ release-lag approximation/i).first()).toBeVisible();
});

test("report builder downloads a named PDF", async ({ page }) => {
  await page.goto("/reports?country=DE");
  await settle(page);
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Download PDF" }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^macropulse-report-de-latest-\d{8}\.pdf$/);
  const file = await download.path();
  const head = (await readFile(file)).subarray(0, 5).toString("latin1");
  expect(head).toBe("%PDF-");
  await expect(page.getByRole("status")).toContainText("Saved macropulse-report-de-latest-");
});
