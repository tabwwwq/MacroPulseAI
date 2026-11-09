import { describe, expect, it } from "vitest";

import { ApiError, unwrap } from "@/lib/api";

function result<T>(status: number, data?: T, error?: unknown) {
  return Promise.resolve({ data, error, response: new Response(null, { status }) });
}

describe("unwrap", () => {
  it("returns data on success", async () => {
    await expect(unwrap(result(200, { ok: true }))).resolves.toEqual({ ok: true });
  });

  it("maps the API error contract to a structured ApiError", async () => {
    const body = {
      error: { code: "unsupported_country", message: "Country 'XX' is not supported.", request_id: "abc12345" },
    };
    const err = await unwrap(result(422, undefined, body)).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ code: "unsupported_country", status: 422, requestId: "abc12345" });
  });

  it("treats a network failure as api_unreachable", async () => {
    const err = await unwrap(Promise.reject(new TypeError("fetch failed"))).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).isUnreachable).toBe(true);
  });

  it("treats a non-contract 5xx (proxy cannot reach FastAPI) as api_unreachable", async () => {
    const err = await unwrap(result(500, undefined, "Internal Server Error")).catch((e: unknown) => e);
    expect((err as ApiError).code).toBe("api_unreachable");
  });

  it("keeps contract 503s (e.g. database_unavailable) distinct from unreachable", async () => {
    const body = { error: { code: "database_unavailable", message: "Run migrations." } };
    const err = await unwrap(result(503, undefined, body)).catch((e: unknown) => e);
    expect((err as ApiError).code).toBe("database_unavailable");
    expect((err as ApiError).isUnreachable).toBe(false);
  });
});
