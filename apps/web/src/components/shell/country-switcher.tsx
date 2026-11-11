"use client";

import * as Select from "@radix-ui/react-select";
import { Check, ChevronDown, Globe } from "lucide-react";

import { SupportBadge } from "@/components/data/support-badge";
import { useAppContext } from "@/lib/context";
import { useCountries } from "@/lib/queries";
import { useHydrated } from "@/lib/use-hydrated";

/**
 * Global country selection. On a country page it navigates to the chosen country; on every other
 * page it sets ?country= so module views (risk, forecasts, …) follow the selection.
 */
export function CountrySwitcher() {
  const query = useCountries();
  const { country, setCountry } = useAppContext();
  // Until hydrated, render exactly what the server rendered (the query was pending there).
  const hydrated = useHydrated();
  const data = hydrated ? query.data : undefined;
  const isPending = !hydrated || query.isPending;
  const isError = hydrated && query.isError;
  const unavailable = isPending || isError || !data;
  const supported = data?.items.some((c) => c.iso2 === country) ?? false;

  return (
    <Select.Root value={supported && country ? country : ""} onValueChange={setCountry} disabled={unavailable}>
      <Select.Trigger
        aria-label={country ? `Country: ${country}` : "Select country"}
        className="inline-flex h-8 min-w-0 items-center gap-2 rounded-lg border border-line-strong bg-surface-2/80 px-2.5 text-sm text-fg shadow-[inset_0_1px_0_rgb(255_255_255/0.05)] transition-colors hover:border-accent/45 hover:bg-elevated disabled:opacity-60 data-[placeholder]:text-fg-muted"
      >
        <Globe className="size-4 shrink-0 text-fg-subtle" aria-hidden />
        <span className="hidden max-w-44 truncate sm:block">
          <Select.Value placeholder={isError ? "Countries unavailable" : isPending ? "Loading…" : "Select country"} />
        </span>
        {/* Compact label on phones; the full name is in the list and in the trigger's aria-label. */}
        <span className="font-mono text-xs sm:hidden" aria-hidden>
          {(supported && country) || "Country"}
        </span>
        <Select.Icon>
          <ChevronDown className="size-4 text-fg-subtle" aria-hidden />
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content
          position="popper"
          sideOffset={6}
          align="end"
          className="z-50 min-w-64 overflow-hidden rounded-xl border border-line-strong bg-elevated p-1 shadow-card"
        >
          <Select.Viewport>
            {data?.items.map((c) => (
              <Select.Item
                key={c.iso2}
                value={c.iso2}
                className="relative flex cursor-pointer select-none items-center gap-3 rounded-lg py-2 pl-2.5 pr-8 text-sm text-fg outline-none data-[highlighted]:bg-surface-2"
              >
                <span className="w-6 font-mono text-xs text-fg-subtle">{c.iso2}</span>
                <Select.ItemText>{c.name}</Select.ItemText>
                <span className="ml-auto">
                  <SupportBadge support={c.support} compact />
                </span>
                <Select.ItemIndicator className="absolute right-2.5">
                  <Check className="size-4 text-accent" aria-hidden />
                </Select.ItemIndicator>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
