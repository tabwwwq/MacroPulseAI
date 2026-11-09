// Re-exports of the generated OpenAPI types. Regenerate with `pnpm gen:types` after API changes.
import type { components } from "./openapi";

export type { components, operations, paths } from "./openapi";

type Schemas = components["schemas"];

export type ApiErrorResponse = Schemas["ErrorResponse"];
export type Country = Schemas["Country"];
export type CountryList = Schemas["CountryList"];
export type CountrySupport = Schemas["CountrySupport"];
export type HealthResponse = Schemas["HealthResponse"];
export type ReadyResponse = Schemas["ReadyResponse"];
export type SourceStatus = Schemas["SourceStatus"];
export type SourceStatusList = Schemas["SourceStatusList"];
export type SupportLevel = CountrySupport["level"];
