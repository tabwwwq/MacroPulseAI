"use client";

import { Segmented } from "@/components/ui/segmented";
import { useAppContext } from "@/lib/context";
import { DEFAULT_RANGE, parseRange, RANGES, type RangeKey } from "@/lib/series";

/** History window shared by every chart on the page, kept in the URL (`?range=`). */
export function useRange(): [RangeKey, (r: RangeKey) => void] {
  const { params, setParam } = useAppContext();
  const range = parseRange(params.get("range"));
  return [range, (r) => setParam("range", r === DEFAULT_RANGE ? null : r)];
}

export function RangeControl({ className }: { className?: string }) {
  const [range, setRange] = useRange();
  return (
    <Segmented
      label="History window"
      options={RANGES.map(({ value, label }) => ({ value, label }))}
      value={range}
      onChange={setRange}
      className={className}
    />
  );
}
