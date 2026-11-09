"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { isValidAsOf } from "@/lib/as-of";

const COUNTRY_PATH = /^\/countries\/([A-Za-z]{2})(?:\/|$)/;
const ISO2 = /^[A-Za-z]{2}$/;

export interface AppContextState {
  /** Selected country (ISO2, upper case) — from the /countries/[code] path or ?country=. */
  country: string | null;
  /** Information cut-off quarter ("2008-Q3"); null = latest. */
  asOf: string | null;
}

/** Pure parser so it can be unit-tested without Next.js. */
export function readContext(pathname: string, params: URLSearchParams, now?: Date): AppContextState {
  const fromPath = COUNTRY_PATH.exec(pathname)?.[1];
  const fromQuery = params.get("country");
  const country = fromPath ?? (fromQuery && ISO2.test(fromQuery) ? fromQuery : null);
  const asOf = params.get("asOf");
  return { country: country ? country.toUpperCase() : null, asOf: isValidAsOf(asOf, now) ? asOf : null };
}

/** Query string carrying the global context to another page (country only off the country pages). */
export function contextQuery(ctx: AppContextState, targetPath: string, extra?: Record<string, string>): string {
  const params = new URLSearchParams();
  if (ctx.country && !targetPath.startsWith("/countries")) params.set("country", ctx.country);
  if (ctx.asOf) params.set("asOf", ctx.asOf);
  for (const [k, v] of Object.entries(extra ?? {})) params.set(k, v);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

/**
 * Global analysis context kept in the URL, so every view is shareable and survives navigation.
 * Components using it must render inside a <Suspense> boundary (useSearchParams).
 */
export function useAppContext() {
  const pathname = usePathname();
  const params = useSearchParams();
  const router = useRouter();
  const ctx = useMemo(() => readContext(pathname, new URLSearchParams(params.toString())), [pathname, params]);

  const setParam = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(params.toString());
      if (value) next.set(key, value);
      else next.delete(key);
      const qs = next.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [params, pathname, router],
  );

  const setCountry = useCallback(
    (iso2: string) => {
      if (pathname.startsWith("/countries")) {
        router.push(`/countries/${iso2.toLowerCase()}${contextQuery({ ...ctx, country: null }, "/countries")}`);
      } else {
        setParam("country", iso2.toUpperCase());
      }
    },
    [ctx, pathname, router, setParam],
  );

  const setAsOf = useCallback((quarter: string | null) => setParam("asOf", quarter), [setParam]);

  /** Href to another page that keeps the current context. */
  const hrefWithContext = useCallback((path: string) => `${path}${contextQuery(ctx, path)}`, [ctx]);

  return { ...ctx, setCountry, setAsOf, setParam, params, hrefWithContext };
}
