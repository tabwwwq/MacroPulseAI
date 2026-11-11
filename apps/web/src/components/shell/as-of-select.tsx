"use client";

import * as Select from "@radix-ui/react-select";
import { CalendarClock, Check, ChevronDown } from "lucide-react";
import { useMemo } from "react";

import { formatAsOf, parseQuarter, selectableQuarters } from "@/lib/as-of";
import { useAppContext } from "@/lib/context";

const LATEST = "latest";

/**
 * Information cut-off for the whole app. "Latest" uses everything published; a past quarter will
 * restrict models and views to data available by the end of that quarter (from Phase 5).
 */
export function AsOfSelect() {
  const { asOf, setAsOf } = useAppContext();
  const byYear = useMemo(() => {
    const groups = new Map<number, string[]>();
    for (const q of selectableQuarters()) {
      const year = parseQuarter(q)?.year ?? 0;
      groups.set(year, [...(groups.get(year) ?? []), q]);
    }
    return [...groups.entries()];
  }, []);

  return (
    <Select.Root value={asOf ?? LATEST} onValueChange={(v) => setAsOf(v === LATEST ? null : v)}>
      <Select.Trigger
        aria-label={`As-of quarter: ${formatAsOf(asOf)}`}
        className="inline-flex h-8 min-w-0 items-center gap-2 rounded-lg border border-line-strong bg-surface-2/80 px-2.5 text-sm text-fg shadow-[inset_0_1px_0_rgb(255_255_255/0.05)] transition-colors hover:border-accent/45 hover:bg-elevated"
      >
        <CalendarClock className="size-4 shrink-0 text-fg-subtle" aria-hidden />
        <span className="hidden text-fg-subtle md:inline">As of</span>
        <span className="font-mono text-xs tabular sm:text-sm">
          <Select.Value>{formatAsOf(asOf)}</Select.Value>
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
          className="z-50 max-h-80 w-56 overflow-hidden rounded-xl border border-line-strong bg-elevated shadow-card"
        >
          <Select.ScrollUpButton className="flex h-6 items-center justify-center text-fg-subtle">▲</Select.ScrollUpButton>
          <Select.Viewport className="p-1">
            <Select.Item
              value={LATEST}
              className="relative flex cursor-pointer select-none items-center rounded-lg py-2 pl-2.5 pr-8 text-sm text-fg outline-none data-[highlighted]:bg-surface-2"
            >
              <Select.ItemText>Latest</Select.ItemText>
              <span className="ml-2 text-xs text-fg-subtle">all published data</span>
              <Select.ItemIndicator className="absolute right-2.5">
                <Check className="size-4 text-accent" aria-hidden />
              </Select.ItemIndicator>
            </Select.Item>
            {byYear.map(([year, quarters]) => (
              <Select.Group key={year}>
                <Select.Label className="px-2.5 pb-1 pt-2 font-mono text-[10.5px] uppercase tracking-[0.14em] text-fg-subtle">
                  {year}
                </Select.Label>
                {quarters.map((q) => (
                  <Select.Item
                    key={q}
                    value={q}
                    className="relative flex cursor-pointer select-none items-center rounded-lg py-1.5 pl-2.5 pr-8 font-mono text-sm text-fg outline-none data-[highlighted]:bg-surface-2"
                  >
                    <Select.ItemText>{formatAsOf(q)}</Select.ItemText>
                    <Select.ItemIndicator className="absolute right-2.5">
                      <Check className="size-4 text-accent" aria-hidden />
                    </Select.ItemIndicator>
                  </Select.Item>
                ))}
              </Select.Group>
            ))}
          </Select.Viewport>
          <Select.ScrollDownButton className="flex h-6 items-center justify-center text-fg-subtle">▼</Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
