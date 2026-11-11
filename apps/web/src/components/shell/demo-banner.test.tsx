import { describe, expect, it } from "vitest";

import type { SourceStatus } from "@macropulse/shared-types";

import { demoSnapshotDate } from "@/components/shell/demo-banner";

const base = {
  name: "x", publisher: "x", docs_url: "", terms_url: "", attribution: "", requires_api_key: false,
  api_key_configured: null, status: "ok", last_attempt_at: null, last_rows_upserted: 1, last_error: null,
} as const;

describe("demoSnapshotDate", () => {
  it("is null for live data and before any sync", () => {
    const live = [{ ...base, id: "eurostat", last_success_at: "2026-11-11T08:00:00Z", data_mode: "live", snapshot_taken_at: null }];
    expect(demoSnapshotDate(live as SourceStatus[])).toBeNull();
    expect(demoSnapshotDate([])).toBeNull();
    expect(demoSnapshotDate(undefined)).toBeNull();
  });

  it("returns the capture date when any source runs on snapshot data", () => {
    const mixed = [
      { ...base, id: "ecb", last_success_at: "2026-11-11T08:00:00Z", data_mode: "live", snapshot_taken_at: null },
      { ...base, id: "fred", last_success_at: "2026-11-09T17:26:16Z", data_mode: "snapshot", snapshot_taken_at: "2026-11-09T17:26:16Z" },
    ];
    expect(demoSnapshotDate(mixed as SourceStatus[])).toBe("2026-11-09");
  });
});
