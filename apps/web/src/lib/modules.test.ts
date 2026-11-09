import { existsSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { MODULES, moduleForPath } from "@/lib/modules";

const APP_DIR = path.resolve(__dirname, "../app");

describe("module registry", () => {
  it("has unique ids and hrefs", () => {
    expect(new Set(MODULES.map((m) => m.id)).size).toBe(MODULES.length);
    expect(new Set(MODULES.map((m) => m.href)).size).toBe(MODULES.length);
  });

  it("links every navigation entry to an existing page (no dead links)", () => {
    for (const m of MODULES) {
      const page = path.join(APP_DIR, m.href === "/" ? "" : m.href, "page.tsx");
      expect(existsSync(page), `${m.href} -> ${page}`).toBe(true);
    }
  });

  it("resolves nested paths to their module", () => {
    expect(moduleForPath("/")?.id).toBe("overview");
    expect(moduleForPath("/countries/de")?.id).toBe("countries");
    expect(moduleForPath("/lab")?.id).toBe("lab");
    expect(moduleForPath("/unknown")).toBeUndefined();
  });
});
