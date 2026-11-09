import { describe, expect, it } from "vitest";

import { formatDateTimeUtc, formatRelative } from "@/lib/format";

describe("formatDateTimeUtc", () => {
  it("renders missing and invalid values as an em dash", () => {
    expect(formatDateTimeUtc(null)).toBe("—");
    expect(formatDateTimeUtc(undefined)).toBe("—");
    expect(formatDateTimeUtc("not-a-date")).toBe("—");
  });

  it("formats in UTC regardless of the viewer's timezone", () => {
    expect(formatDateTimeUtc("2026-01-05T06:02:00+00:00")).toBe("05 Jan 2026, 06:02 UTC");
    expect(formatDateTimeUtc("2026-01-05T07:02:00+01:00")).toBe("05 Jan 2026, 06:02 UTC");
  });
});

describe("formatRelative", () => {
  const now = Date.parse("2026-11-08T12:00:00Z");

  it("uses coarse units", () => {
    expect(formatRelative("2026-11-08T09:00:00Z", now)).toBe("3 hours ago");
    expect(formatRelative("2026-11-07T12:00:00Z", now)).toBe("yesterday");
    expect(formatRelative("2026-11-08T11:59:40Z", now)).toBe("just now");
  });

  it("renders missing values as an em dash", () => {
    expect(formatRelative(null, now)).toBe("—");
  });
});
