import type { ApiErrorResponse } from "@macropulse/shared-types";

import { ApiError, UNREACHABLE_MESSAGE } from "@/lib/api";
import { downloadDataUrl } from "@/lib/export";

export type ReportFormat = "pdf" | "csv" | "json";

export interface ReportRequest {
  country: string;
  asOf: string | null;
  format: ReportFormat;
}

/** `attachment; filename="macropulse-report-de-latest-20261110.pdf"` → the filename, if safe. */
export function filenameFromDisposition(header: string | null, fallback: string): string {
  const match = /filename="([A-Za-z0-9._-]+)"/.exec(header ?? "");
  return match?.[1] ?? fallback;
}

function isErrorBody(value: unknown): value is ApiErrorResponse {
  return typeof value === "object" && value !== null && "error" in value;
}

/** POST /api/reports/generate and return the file; errors become ApiError (with the API's code). */
export async function fetchReport(
  { country, asOf, format }: ReportRequest,
  fetcher: typeof fetch = fetch,
): Promise<{ blob: Blob; filename: string }> {
  let response: Response;
  try {
    response = await fetcher("/api/reports/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country, format, ...(asOf ? { as_of: asOf } : {}) }),
    });
  } catch {
    throw new ApiError("api_unreachable", UNREACHABLE_MESSAGE, 0);
  }
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    if (isErrorBody(body)) {
      throw new ApiError(body.error.code, body.error.message, response.status, body.error.request_id ?? null);
    }
    throw response.status >= 500
      ? new ApiError("api_unreachable", UNREACHABLE_MESSAGE, response.status)
      : new ApiError("http_error", `Request failed with status ${response.status}.`, response.status);
  }
  const fallback = `macropulse-report-${country.toLowerCase()}-${asOf ?? "latest"}.${format}`;
  return { blob: await response.blob(), filename: filenameFromDisposition(response.headers.get("Content-Disposition"), fallback) };
}

/** Generate and save a report in the browser. */
export async function downloadReport(request: ReportRequest): Promise<string> {
  const { blob, filename } = await fetchReport(request);
  const url = URL.createObjectURL(blob);
  try {
    downloadDataUrl(filename, url);
  } finally {
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return filename;
}
