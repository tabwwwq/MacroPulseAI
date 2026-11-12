import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { horizontalOverflow, settle } from "./support";

const CARD = "With the figures as first published";
const US_2022 = "/history?country=US&asOf=2022-Q3&horizon=4";

test.describe("Crisis time machine on the figures as first published (ALFRED)", () => {
  test("without stored vintages the card says how to sync and shows no estimate", async ({ page }) => {
    await page.route("**/api/history/vintage-replay?*", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "vintages_not_synced",
            message: "No ALFRED vintages are stored for GDPC1. Run `uv run macropulse vintages-sync` on the server (needs FRED_API_KEY).",
            details: {},
            request_id: "e2e-vintage-replay",
          },
        }),
      }),
    );
    await page.goto(US_2022);
    await settle(page);
    const card = page.getByRole("region", { name: CARD });
    test.skip((await page.getByText(/What the model said at/).count()) === 0, "no trained model in this environment");
    await expect(card.getByText("First-release comparison unavailable")).toBeVisible();
    await expect(card.getByText(/macropulse vintages-sync/)).toBeVisible();
    await expect(card.getByRole("table")).toHaveCount(0);
  });

  test("no first-release comparison outside the United States", async ({ page }) => {
    await page.goto("/history?country=DE&asOf=2022-Q3&horizon=4");
    await settle(page);
    await expect(page.getByRole("region", { name: CARD })).toHaveCount(0);
  });

  test("with stored vintages the comparison is complete, fits and is accessible", async ({ page }) => {
    const probe = await page.request.get("/api/history/vintage-replay?country=US&horizon=4&as_of=2022-Q3");
    test.skip(probe.status() !== 200, "no vintages or model in this environment (needs FRED_API_KEY and training)");
    await page.goto(US_2022);
    await settle(page);
    const card = page.getByRole("region", { name: CARD });
    await expect(card.getByRole("group", { name: "As first published" })).toBeVisible();
    await expect(card.getByRole("table", { name: "Inputs: today's data versus first published" })).toBeVisible();
    await expect(card.getByText(/^Not revised, identical in both:/)).toBeVisible();
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
    const result = await new AxeBuilder({ page })
      .include(`[aria-label="${CARD}"]`)
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious.map((v) => v.id)).toEqual([]);
  });
});
