import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { horizontalOverflow, ROUTES, settle, watchConsole } from "./support";

for (const route of ROUTES) {
  test.describe(route, () => {
    test("renders without errors and without horizontal overflow", async ({ page }) => {
      const errors = watchConsole(page);
      await page.goto(route);
      await settle(page);
      expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
      expect(errors).toEqual([]);
    });

    test("has no serious or critical accessibility violations", async ({ page }) => {
      await page.goto(route);
      await settle(page);
      const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      const serious = result.violations
        .filter((v) => v.impact === "serious" || v.impact === "critical")
        .map((v) => `${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
      expect(serious).toEqual([]);
    });
  });
}
