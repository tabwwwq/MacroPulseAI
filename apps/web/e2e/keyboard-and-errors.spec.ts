import { expect, test } from "@playwright/test";

import { settle } from "./support";

test.describe("keyboard", () => {
  test("the first Tab reaches 'Skip to content', which moves focus to the main region", async ({ page }) => {
    await page.goto("/forecasts?country=DE");
    await settle(page);
    await page.keyboard.press("Tab");
    const skip = page.getByRole("link", { name: "Skip to content" });
    await expect(skip).toBeFocused();
    await page.keyboard.press("Enter");
    await expect.poll(() => page.evaluate(() => document.activeElement?.id)).toBe("main");
  });

  test("segmented controls follow the arrow keys and keep the choice in the URL", async ({ page }) => {
    await page.goto("/forecasts?country=DE");
    await settle(page);
    const gdp = page.getByRole("radio", { name: "GDP growth" });
    await gdp.focus();
    await page.keyboard.press("ArrowRight");
    await expect(page.getByRole("radio", { name: "Inflation" })).toBeFocused();
    await expect(page).toHaveURL(/metric=inflation_yoy/);
  });
});

test.describe("failure paths", () => {
  test("an unreachable API is reported with a working retry", async ({ page }) => {
    await page.route("**/api/**", (route) => route.abort("connectionrefused"));
    await page.goto("/countries");
    await expect(page.getByText("API unreachable").first()).toBeVisible();
    await page.unroute("**/api/**");
    await page.getByRole("button", { name: "Retry" }).first().click();
    await expect(page.getByText("API unreachable")).toHaveCount(0);
  });

  test("a series that is not synced shows an explicit state, not a made-up chart", async ({ page }) => {
    await page.route("**/api/indicators?*", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "data_not_synced",
            message: "No observations stored for this series. Run `uv run macropulse data-sync`.",
            details: null,
            request_id: "e2e-not-synced",
          },
        }),
      }),
    );
    await page.goto("/countries/de?tab=growth");
    await expect(page.getByText("Not synced yet").first()).toBeVisible();
  });

  test("an untrained model shows the training instruction instead of a probability", async ({ page }) => {
    await page.route("**/api/recession/predict?*", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "model_not_trained",
            message: "No model has been trained yet. Run `uv run macropulse train` on the server.",
            details: null,
            request_id: "e2e-not-trained",
          },
        }),
      }),
    );
    await page.goto("/recession?country=DE");
    await expect(page.getByText("Model not trained").first()).toBeVisible();
    await expect(page.getByText("macropulse train").first()).toBeVisible();
  });
});
