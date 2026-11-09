import { useQuery } from "@tanstack/react-query";

import { api, ApiError, fetchReady, unwrap } from "@/lib/api";

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
};

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
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => unwrap(api.GET("/api/health")),
    refetchInterval: 60_000,
  });
}

export function useReady() {
  return useQuery({
    queryKey: queryKeys.ready,
    queryFn: fetchReady,
    refetchInterval: 30_000,
  });
}

export function useCountries() {
  return useQuery({
    queryKey: queryKeys.countries,
    queryFn: () => unwrap(api.GET("/api/countries")),
    staleTime: 5 * 60_000,
  });
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
  return useQuery({
    queryKey: queryKeys.sources,
    queryFn: () => unwrap(api.GET("/api/sources/status")),
    refetchInterval: 60_000,
  });
}
