import createClient from "openapi-fetch";

import type { ApiErrorResponse, paths, ReadyResponse } from "@macropulse/shared-types";

/**
 * Typed client generated from the FastAPI OpenAPI schema. The browser calls same-origin `/api/*`,
 * which the Next.js server proxies to FastAPI (see next.config.ts) — no backend URL in the bundle.
 */
export const api = createClient<paths>({ baseUrl: "" });

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId: string | null;

  constructor(code: string, message: string, status: number, requestId: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }

  get isUnreachable(): boolean {
    return this.code === "api_unreachable";
  }
}

export const UNREACHABLE_MESSAGE =
  "Cannot reach the MacroPulse API. Start it with `pnpm dev` (or `pnpm dev:api`) and retry.";

function isErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null || !("error" in value)) return false;
  const err = (value as { error: unknown }).error;
  return typeof err === "object" && err !== null && "code" in err && "message" in err;
}

function isReadyResponse(value: unknown): value is ReadyResponse {
  return typeof value === "object" && value !== null && "status" in value && "checks" in value;
}

type FetchResult<T> = { data?: T; error?: unknown; response: Response };

function toApiError(error: unknown, response: Response): ApiError {
  if (isErrorResponse(error)) {
    return new ApiError(error.error.code, error.error.message, response.status, error.error.request_id ?? null);
  }
  // A non-contract 5xx means the Next.js proxy could not reach FastAPI.
  if (response.status >= 500) {
    return new ApiError("api_unreachable", UNREACHABLE_MESSAGE, response.status);
  }
  return new ApiError("http_error", `Request failed with status ${response.status}.`, response.status);
}

/** Resolve an openapi-fetch call to its data, or throw a structured `ApiError`. */
export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  let result: FetchResult<T>;
  try {
    result = await request;
  } catch {
    throw new ApiError("api_unreachable", UNREACHABLE_MESSAGE, 0);
  }
  if (result.response.ok && result.data !== undefined) return result.data;
  throw toApiError(result.error, result.response);
}

/** `/api/ready` answers 503 with a ReadyResponse body when not ready; surface it as data. */
export async function fetchReady(): Promise<ReadyResponse> {
  let result: FetchResult<ReadyResponse>;
  try {
    result = await api.GET("/api/ready");
  } catch {
    throw new ApiError("api_unreachable", UNREACHABLE_MESSAGE, 0);
  }
  if (result.data !== undefined) return result.data;
  if (result.response.status === 503 && isReadyResponse(result.error)) return result.error;
  throw toApiError(result.error, result.response);
}
