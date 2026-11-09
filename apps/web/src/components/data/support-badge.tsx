import { CircleCheck, CircleDashed, CircleDot } from "lucide-react";

import type { CountrySupport, SupportLevel } from "@macropulse/shared-types";

import { Badge } from "@/components/ui/badge";

const CONFIG: Record<SupportLevel, { label: string; tone: "ok" | "warn" | "neutral"; Icon: typeof CircleCheck }> = {
  full: { label: "Full support", tone: "ok", Icon: CircleCheck },
  partial: { label: "Partial support", tone: "warn", Icon: CircleDot },
  unavailable: { label: "No data yet", tone: "neutral", Icon: CircleDashed },
};

/** Support level as icon + text (never colour alone). `compact` drops the word "support". */
export function SupportBadge({ support, compact = false }: { support: CountrySupport; compact?: boolean }) {
  const { label, tone, Icon } = CONFIG[support.level];
  const text = compact ? label.replace(" support", "") : label;
  return (
    <Badge tone={tone} dashed={support.level === "unavailable"} title={support.reason}>
      <Icon className="size-3" aria-hidden />
      {text}
    </Badge>
  );
}
