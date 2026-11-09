import { useQuery } from "@tanstack/react-query";

import { api, fetchReady, unwrap } from "@/lib/api";

export const queryKeys = {
  health: ["health"] as const,
  ready: ["ready"] as const,
  countries: ["countries"] as const,
  country: (iso2: string) => ["countries", iso2.toUpperCase()] as const,
  sources: ["sources", "status"] as const,
};

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

export function useSourcesStatus() {
  return useQuery({
    queryKey: queryKeys.sources,
    queryFn: () => unwrap(api.GET("/api/sources/status")),
    refetchInterval: 60_000,
  });
}
