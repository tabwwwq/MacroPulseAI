import { afterEach, describe, expect, it, vi } from "vitest";

import type { ChartSeries } from "@/components/charts/types";
import { downloadDataUrl, downloadText, seriesToCsv } from "@/lib/export";

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("seriesToCsv", () => {
  it("sorts the union of periods, includes units and leaves null/missing cells empty", () => {
    const fixture: ChartSeries[] = [
      { id: "a", name: "Test A", unit: "%", points: [
        { period: "2026-Q3", value: null },
        { period: "2026-Q1", value: 0 },
      ] },
      { id: "b", name: "Test B", unit: "index", points: [
        { period: "2026-Q2", value: -2.5 },
        { period: "2026-Q3", value: 103 },
      ] },
    ];
    expect(seriesToCsv(fixture)).toBe(
      "period,Test A (%),Test B (index)\r\n2026-Q1,0,\r\n2026-Q2,,-2.5\r\n2026-Q3,,103\r\n",
    );
  });

  it("quotes commas, quotes and newlines according to RFC 4180", () => {
    expect(seriesToCsv([
      { id: "a", name: 'Test, "quoted"', unit: "%, annual", points: [{ period: "2026-09", value: 1 }] },
      { id: "b", name: "Test\r\nmultiline", unit: "", points: [] },
    ])).toBe('period,"Test, ""quoted"" (%, annual)","Test\r\nmultiline"\r\n2026-09,1,\r\n');
  });

  it("preserves missing observations without inventing zeroes", () => {
    expect(seriesToCsv([{ id: "a", name: "Test", unit: "%", points: [{ period: "2026-09", value: null }] }]))
      .toBe("period,Test (%)\r\n2026-09,\r\n");
    expect(seriesToCsv([])).toBe("period\r\n");
  });
});

describe("download helpers", () => {
  it("clicks a temporary link with the requested PNG filename and URL", () => {
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      expect(this.download).toBe("test.png");
      expect(this.href).toBe("data:image/png;base64,dGVzdA==");
      expect(this.isConnected).toBe(true);
    });
    downloadDataUrl("test.png", "data:image/png;base64,dGVzdA==");
    expect(click).toHaveBeenCalledOnce();
    expect(document.querySelector("a[download]")).toBeNull();
  });

  it("downloads a text Blob and releases its URL after the download starts", () => {
    vi.useFakeTimers();
    const createObjectURL = vi.fn<(blob: Blob) => string>(() => "blob:test-csv");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", class extends URL {
      static createObjectURL = createObjectURL;
      static revokeObjectURL = revokeObjectURL;
    });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      expect(this.download).toBe("test.csv");
      expect(this.href).toBe("blob:test-csv");
    });
    downloadText("test.csv", "period\r\n");
    expect(click).toHaveBeenCalledOnce();
    const blob = createObjectURL.mock.calls[0]?.[0];
    expect(blob).toBeInstanceOf(Blob);
    expect(blob).toHaveProperty("type", "text/csv;charset=utf-8");
    expect(revokeObjectURL).not.toHaveBeenCalled();
    vi.runAllTimers();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:test-csv");
  });
});
