import { keepPreviousData, useQuery } from "@tanstack/react-query";

import type { ScenarioRequest } from "@macropulse/shared-types";

import { api, ApiError, fetchReady, unwrap } from "@/lib/api";
import { useHydrated } from "@/lib/use-hydrated";

export const queryKeys = {
  health: ["health"] as const,
  ready: ["ready"] as const,
  countries: ["countries"] as const,
  country: (iso2: string) => ["countries", iso2.toUpperCase()] as const,
  sources: ["sources", "status"] as const,
  catalog: (iso2: string | null) => ["indicators", "catalog", iso2 ?? "all"] as const,
  series: (iso2: string, indicator: string, start?: string, end?: string) =>
    ["indicators", "series", iso2.toUpperCase(), indicator, start ?? "", end ?? ""] as const,
  summary: (iso2: string, asOf: string | null) => ["countries", iso2.toUpperCase(), "summary", asOf ?? "latest"] as const,
  quality: (iso2: string | null) => ["data-quality", iso2 ?? "all"] as const,
  models: ["models", "latest"] as const,
  estimate: (iso2: string, horizon: number, asOf: string | null) =>
    ["recession", "predict", iso2.toUpperCase(), horizon, asOf ?? "latest"] as const,
  history: (iso2: string, horizon: number) => ["recession", "history", iso2.toUpperCase(), horizon] as const,
  modelDetail: (id: string) => ["models", id, "metrics"] as const,
  modelCurves: (id: string) => ["models", id, "curves"] as const,
  forecast: (iso2: string, metric: string, horizon: number, asOf: string | null) =>
    ["forecasts", iso2.toUpperCase(), metric, horizon, asOf ?? "latest"] as const,
  scenarioSpec: ["scenarios", "spec"] as const,
  replay: (iso2: string, horizon: number, asOf: string) => ["history", "replay", iso2.toUpperCase(), horizon, asOf] as const,
  episodes: (iso2: string, horizon: number) => ["history", "episodes", iso2.toUpperCase(), horizon] as const,
  vintageReplay: (iso2: string, horizon: number, asOf: string) =>
    ["history", "vintage-replay", iso2.toUpperCase(), horizon, asOf] as const,
  presets: ["history", "presets"] as const,
  revisions: (iso2: string, indicator: string) => ["vintages", "revisions", iso2.toUpperCase(), indicator] as const,
  scenario: (r: ScenarioRequest | null) =>
    ["scenarios", "evaluate", r?.country ?? "", r?.horizon ?? 0, r?.as_of ?? "latest", JSON.stringify(r?.shocks ?? {})] as const,
};

/**
 * Queries the shell also uses (top bar, footer) can resolve while a page's Suspense boundary is
 * still hydrating; the page's first client render would then see data the server HTML never had
 * and React would report a hydration mismatch. Until hydration completes, such a query is
 * reported as pending — exactly what the server rendered.
 */
function usePendingUntilHydrated<T extends { data: unknown }>(result: T): T {
  const hydrated = useHydrated();
  if (hydrated) return result;
  return {
    ...result,
    data: undefined,
    error: null,
    status: "pending",
    isPending: true,
    isLoading: true,
    isSuccess: false,
    isError: false,
  } as T;
}

/** 404/503 are answers (not trained, inputs not published), not transient failures. */
function retryUnlessAnswer(count: number, error: unknown): boolean {
  return !(error instanceof ApiError && [404, 422, 503].includes(error.status)) && count < 2;
}

/** Live inference: the published model's probability for one country, horizon and as-of. */
export function useRecessionEstimate(iso2: string, horizon: 2 | 4, asOf: string | null) {
  return useQuery({
    queryKey: queryKeys.estimate(iso2, horizon, asOf),
    queryFn: () =>
      unwrap(
        api.GET("/api/recession/predict", {
          params: { query: { country: iso2, horizon, ...(asOf ? { as_of: asOf } : {}) } },
        }),
      ),
    enabled: /^[A-Za-z]{2}$/.test(iso2),
    staleTime: 5 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** Out-of-sample walk-forward probabilities plus realised technical recessions. */
export function useRecessionHistory(iso2: string, horizon: 2 | 4) {
  return useQuery({
    queryKey: queryKeys.history(iso2, horizon),
    queryFn: () => unwrap(api.GET("/api/recession/history", { params: { query: { country: iso2, horizon } } })),
    staleTime: 5 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** Forecast paths of every model, empirical intervals and rolling-origin backtest diagnostics. */
export function useForecast(iso2: string | null, metric: string, horizon: number, asOf: string | null) {
  return useQuery({
    queryKey: queryKeys.forecast(iso2 ?? "", metric, horizon, asOf),
    queryFn: () =>
      unwrap(
        api.GET("/api/forecasts", {
          params: { query: { country: iso2 ?? "", metric, horizon, ...(asOf ? { as_of: asOf } : {}) } },
        }),
      ),
    enabled: Boolean(iso2 && /^[A-Za-z]{2}$/.test(iso2)),
    staleTime: 5 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** Shocks the scenario lab accepts, with their bounds and how each maps onto model inputs. */
export function useScenarioSpec() {
  return useQuery({
    queryKey: queryKeys.scenarioSpec,
    queryFn: () => unwrap(api.GET("/api/scenarios/spec")),
    staleTime: Infinity,
  });
}

/** Baseline vs shocked probability of the published model. Keeps the previous answer on screen
 *  while a new slider position is evaluated. */
export function useScenarioEvaluation(request: ScenarioRequest | null) {
  return useQuery({
    queryKey: queryKeys.scenario(request),
    queryFn: () => unwrap(api.POST("/api/scenarios/evaluate", { body: request as ScenarioRequest })),
    enabled: request !== null,
    placeholderData: keepPreviousData,
    staleTime: 5 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** Walk-forward estimate at a past as-of quarter with the inputs known then and what followed. */
export function useReplay(iso2: string, horizon: 2 | 4, asOf: string) {
  return useQuery({
    queryKey: queryKeys.replay(iso2, horizon, asOf),
    queryFn: () =>
      unwrap(api.GET("/api/history/replay", { params: { query: { country: iso2, horizon, as_of: asOf } } })),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** US only: the same walk-forward fold model scored on GDP, CPI and unemployment as first published. */
export function useVintageReplay(iso2: string, horizon: 2 | 4, asOf: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.vintageReplay(iso2, horizon, asOf),
    queryFn: () =>
      unwrap(api.GET("/api/history/vintage-replay", { params: { query: { country: iso2, horizon, as_of: asOf } } })),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 10 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** First release versus current value per period, from stored ALFRED vintages (US only). */
export function useRevisions(iso2: string, indicator: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.revisions(iso2, indicator),
    queryFn: () =>
      unwrap(api.GET("/api/vintages/revisions", { params: { query: { country: iso2, indicator } } })),
    enabled,
    staleTime: 10 * 60_000,
    retry: retryUnlessAnswer,
  });
}

/** Realised technical recessions (warned / missed / not evaluable) and false alarms. */
export function useReplayEpisodes(iso2: string, horizon: 2 | 4) {
  return useQuery({
    queryKey: queryKeys.episodes(iso2, horizon),
    queryFn: () => unwrap(api.GET("/api/history/episodes", { params: { query: { country: iso2, horizon } } })),
    staleTime: 5 * 60_000,
    retry: retryUnlessAnswer,
  });
}

export function useCrisisPresets() {
  return useQuery({
    queryKey: queryKeys.presets,
    queryFn: () => unwrap(api.GET("/api/history/presets")),
    staleTime: Infinity,
  });
}

export function useModelDetail(id: string | null) {
  return useQuery({
    queryKey: queryKeys.modelDetail(id ?? ""),
    queryFn: () => unwrap(api.GET("/api/models/{model_id}/metrics", { params: { path: { model_id: id ?? "" } } })),
    enabled: Boolean(id),
    staleTime: 5 * 60_000,
  });
}

export function useModelCurves(id: string | null) {
  return useQuery({
    queryKey: queryKeys.modelCurves(id ?? ""),
    queryFn: () => unwrap(api.GET("/api/models/{model_id}/curves", { params: { path: { model_id: id ?? "" } } })),
    enabled: Boolean(id),
    staleTime: 5 * 60_000,
  });
}

/** Model versions of the latest training run (empty list + note when nothing is trained). */
export function useModels() {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: () => unwrap(api.GET("/api/models", { params: { query: { run: "latest" } } })),
    staleTime: 5 * 60_000,
  });
}

export interface SeriesQuery {
  country: string;
  indicator: string;
  start?: string;
  end?: string;
}

export function seriesQueryOptions({ country, indicator, start, end }: SeriesQuery) {
  return {
    queryKey: queryKeys.series(country, indicator, start, end),
    queryFn: () =>
      unwrap(
        api.GET("/api/indicators", {
          params: { query: { country, indicator, ...(start ? { start } : {}), ...(end ? { end } : {}) } },
        }),
      ),
    staleTime: 5 * 60_000,
    // 404/503 are answers ("not published", "not synced"), not transient failures.
    retry: (count: number, error: unknown) =>
      !(error instanceof ApiError && [404, 422, 503].includes(error.status)) && count < 2,
  };
}

/** Stored official series for one country/indicator, derived transparently by the API. */
export function useIndicatorSeries(q: SeriesQuery | null) {
  return useQuery({
    ...seriesQueryOptions(q ?? { country: "", indicator: "" }),
    enabled: q !== null,
  });
}

/** Headline KPIs: latest stored value, change, staleness and provenance per KPI indicator. */
export function useCountrySummary(iso2: string, asOf: string | null) {
  return useQuery({
    queryKey: queryKeys.summary(iso2, asOf),
    queryFn: () =>
      unwrap(
        api.GET("/api/countries/{iso2}/summary", {
          params: { path: { iso2 }, query: asOf ? { as_of: asOf } : {} },
        }),
      ),
    staleTime: 5 * 60_000,
  });
}

/** Lineage and latest quality checks for the series behind one country (or all of them). */
export function useDataQuality(iso2: string | null) {
  return useQuery({
    queryKey: queryKeys.quality(iso2),
    queryFn: () =>
      iso2
        ? unwrap(api.GET("/api/countries/{iso2}/data-quality", { params: { path: { iso2 } } }))
        : unwrap(api.GET("/api/data-quality")),
    staleTime: 60_000,
  });
}

export function useHealth() {
  return usePendingUntilHydrated(
    useQuery({
      queryKey: queryKeys.health,
      queryFn: () => unwrap(api.GET("/api/health")),
      refetchInterval: 60_000,
    }),
  );
}

export function useReady() {
  return usePendingUntilHydrated(
    useQuery({
      queryKey: queryKeys.ready,
      queryFn: fetchReady,
      refetchInterval: 30_000,
    }),
  );
}

export function useCountries() {
  return usePendingUntilHydrated(
    useQuery({
      queryKey: queryKeys.countries,
      queryFn: () => unwrap(api.GET("/api/countries")),
      staleTime: 5 * 60_000,
    }),
  );
}

export function useCountry(iso2: string) {
  return useQuery({
    queryKey: queryKeys.country(iso2),
    queryFn: () => unwrap(api.GET("/api/countries/{iso2}", { params: { path: { iso2 } } })),
    staleTime: 5 * 60_000,
  });
}

/** Indicator definitions + verified source mappings + ingestion state (one country or all). */
export function useCatalog(iso2: string | null) {
  return useQuery({
    queryKey: queryKeys.catalog(iso2),
    queryFn: () =>
      unwrap(api.GET("/api/indicators/catalog", { params: { query: iso2 ? { country: iso2 } : {} } })),
    staleTime: 5 * 60_000,
  });
}

export function useSourcesStatus() {
  return usePendingUntilHydrated(
    useQuery({
      queryKey: queryKeys.sources,
      queryFn: () => unwrap(api.GET("/api/sources/status")),
      refetchInterval: 60_000,
    }),
  );
}
