import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api";
import { fetchReport, filenameFromDisposition } from "@/lib/reports";

describe("filenameFromDisposition", () => {
  it("takes the server's descriptive filename", () => {
    expect(filenameFromDisposition('attachment; filename="macropulse-report-de-2008-Q2-20261110.pdf"', "x.pdf")).toBe(
      "macropulse-report-de-2008-Q2-20261110.pdf",
    );
  });

  it("falls back when the header is missing or unsafe", () => {
    expect(filenameFromDisposition(null, "fallback.pdf")).toBe("fallback.pdf");
    expect(filenameFromDisposition('attachment; filename="../../evil.exe"', "fallback.pdf")).toBe("fallback.pdf");
  });
});

describe("fetchReport", () => {
  it("posts the selection and returns the file", async () => {
    let sent: { url: string; body: unknown } | null = null;
    const fake = (async (url: string, init?: RequestInit) => {
      sent = { url, body: JSON.parse(String(init?.body)) };
      return new Response("%PDF-1.7", {
        status: 200,
        headers: { "Content-Disposition": 'attachment; filename="macropulse-report-de-latest-20261110.pdf"' },
      });
    }) as typeof fetch;
    const { blob, filename } = await fetchReport({ country: "DE", asOf: null, format: "pdf" }, fake);
    expect(sent).toEqual({ url: "/api/reports/generate", body: { country: "DE", format: "pdf" } });
    expect(filename).toBe("macropulse-report-de-latest-20261110.pdf");
    expect(await blob.text()).toBe("%PDF-1.7");
  });

  it("surfaces the API error contract", async () => {
    const fake = (async () =>
      new Response(JSON.stringify({ error: { code: "invalid_as_of", message: "As-of quarter is in the future.", request_id: "r1" } }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      })) as typeof fetch;
    await expect(fetchReport({ country: "DE", asOf: "2099-Q1", format: "pdf" }, fake)).rejects.toMatchObject({
      code: "invalid_as_of",
      status: 422,
      requestId: "r1",
    });
  });

  it("reports an unreachable API", async () => {
    const fake = (async () => {
      throw new TypeError("network down");
    }) as typeof fetch;
    await expect(fetchReport({ country: "DE", asOf: null, format: "csv" }, fake)).rejects.toBeInstanceOf(ApiError);
  });
});
