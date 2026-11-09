"use client";

import * as Select from "@radix-ui/react-select";
import { Check, ChevronDown, Globe } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

import { SupportBadge } from "@/components/data/support-badge";
import { useCountries } from "@/lib/queries";

const COUNTRY_PATH = /^\/countries\/([A-Za-z]{2})(?:\/|$)/;

/** Navigates to the selected country's profile; reflects the country currently being viewed. */
export function CountrySwitcher() {
  const { data, isPending, isError } = useCountries();
  const pathname = usePathname();
  const router = useRouter();
  const current = COUNTRY_PATH.exec(pathname)?.[1]?.toUpperCase() ?? "";
  const unavailable = isPending || isError || !data;

  return (
    <Select.Root
      value={current}
      onValueChange={(iso2) => router.push(`/countries/${iso2.toLowerCase()}`)}
      disabled={unavailable}
    >
      <Select.Trigger
        aria-label="Select country"
        className="inline-flex h-8 min-w-0 items-center gap-2 rounded-lg border border-line-strong bg-surface-2 px-2.5 text-sm text-fg hover:bg-elevated disabled:opacity-60 data-[placeholder]:text-fg-muted"
      >
        <Globe className="size-4 shrink-0 text-fg-subtle" aria-hidden />
        <span className="hidden max-w-44 truncate sm:block">
          <Select.Value placeholder={isError ? "Countries unavailable" : isPending ? "Loading…" : "Select country"} />
        </span>
        {/* Compact label on phones; the full name is in the list and in the trigger's aria-label. */}
        <span className="font-mono text-xs sm:hidden" aria-hidden>
          {current || "Country"}
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
