import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { settle } from "./support";

const CARD = "Real GDP growth (q/q): first release vs today";

test.describe("US revision history (ALFRED)", () => {
  test("without stored vintages the card says how to sync, and shows no chart", async ({ page }) => {
    await page.route("**/api/vintages/revisions?*", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "vintages_not_synced",
            message: "No ALFRED vintages are stored yet. Run `uv run macropulse vintages-sync` on the server.",
            details: { fred_api_key_configured: false },
            request_id: "e2e-vintages",
          },
        }),
      }),
    );
    await page.goto("/countries/us?tab=growth");
    await settle(page);
    await expect(page.getByText("Revision history not synced")).toBeVisible();
    await expect(page.getByText(/macropulse vintages-sync/)).toBeVisible();
    await expect(page.getByRole("region", { name: CARD })).toHaveCount(0);
  });

  test("no revision card outside the United States", async ({ page }) => {
    await page.goto("/countries/de?tab=growth");
    await settle(page);
    await expect(page.getByText(/first release vs today|Revision history/)).toHaveCount(0);
  });

  test("with stored vintages the card is complete and accessible", async ({ page }) => {
    const probe = await page.request.get("/api/vintages/revisions?country=US&indicator=real_gdp_qoq");
    test.skip(probe.status() !== 200, "no vintages stored in this environment (needs FRED_API_KEY)");
    await page.goto("/countries/us?tab=growth");
    await settle(page);
    const card = page.getByRole("region", { name: CARD });
    await expect(card).toBeVisible();
    await expect(card.getByRole("table", { name: "Largest revisions" })).toBeVisible();
    await expect(card.getByText(/first releases$/).first()).toBeVisible();
    const result = await new AxeBuilder({ page })
      .include(`[aria-label="${CARD}"]`)
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    const serious = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious.map((v) => v.id)).toEqual([]);
  });
});
