import { describe, expect, it } from "vitest";

import { contextQuery, readContext } from "@/lib/context";

const NOW = new Date("2026-11-09T12:00:00Z");
const p = (qs: string) => new URLSearchParams(qs);

describe("readContext", () => {
  it("takes the country from the country page path first", () => {
    expect(readContext("/countries/de", p("country=FR"), NOW).country).toBe("DE");
  });

  it("falls back to a well-formed ?country= elsewhere", () => {
    expect(readContext("/recession", p("country=nl"), NOW).country).toBe("NL");
    expect(readContext("/recession", p("country=NLD"), NOW).country).toBeNull();
  });

  it("drops invalid or future as-of quarters (latest instead)", () => {
    expect(readContext("/", p("asOf=2008-Q3"), NOW).asOf).toBe("2008-Q3");
    expect(readContext("/", p("asOf=2030-Q1"), NOW).asOf).toBeNull();
    expect(readContext("/", p("asOf=oops"), NOW).asOf).toBeNull();
  });
});

describe("contextQuery", () => {
  it("carries country and as-of to module pages", () => {
    expect(contextQuery({ country: "DE", asOf: "2008-Q3" }, "/recession")).toBe("?country=DE&asOf=2008-Q3");
  });

  it("omits the country param on country pages (the path carries it)", () => {
    expect(contextQuery({ country: "DE", asOf: null }, "/countries")).toBe("");
  });

  it("returns an empty string without context", () => {
    expect(contextQuery({ country: null, asOf: null }, "/lab")).toBe("");
  });
});
