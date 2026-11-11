import { useId, type JSX } from "react";

/** ECG-like polyline across a width x height box: flat baseline with `beats` evenly spaced heartbeats. */
export function pulsePath(width: number, height: number, beats: number): string {
  const baseline = round2(0.6 * height);
  const parts: string[] = [`M 0 ${baseline}`];

  for (let k = 0; k < beats; k += 1) {
    const cx = (k + 0.5) * width / beats;
    const vertices: [number, number][] = [
      [cx - 16, baseline],
      [cx - 8, baseline - 0.12 * height],
      [cx, baseline - 0.48 * height],
      [cx + 8, baseline + 0.28 * height],
      [cx + 16, baseline],
    ];
    for (const [x, y] of vertices) {
      parts.push(`L ${round2(x)} ${round2(y)}`);
    }
  }

  parts.push(`L ${round2(width)} ${baseline}`);
  return parts.join(" ");
}

export function PulseLine({ className }: { className?: string }): JSX.Element {
  const id = useId().replace(/:/g, "");
  const gradientId = `pulse-gradient-${id}`;
  const filterId = `pulse-glow-${id}`;

  const d = pulsePath(600, 120, 3);
  const gradient = `url(#${gradientId})`;

  return (
    <svg
      viewBox="0 0 600 120"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      fill="none"
      className={className}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="var(--color-iris)" />
          <stop offset="50%" stopColor="var(--color-accent)" />
          <stop offset="100%" stopColor="var(--color-ok)" />
        </linearGradient>
        <filter id={filterId} x="-10%" y="-50%" width="120%" height="200%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>
      <path
        data-part="base"
        d={d}
        stroke="var(--color-line-strong)"
        strokeWidth={1.25}
        vectorEffect="non-scaling-stroke"
      />
      <path
        d={d}
        stroke={gradient}
        strokeWidth={4}
        strokeDasharray="70 190"
        className="animate-trace"
        opacity={0.7}
        filter={`url(#${filterId})`}
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
      <path
        data-part="trace"
        d={d}
        stroke={gradient}
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="70 190"
        className="animate-trace"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

function round2(x: number): number {
  return Number(x.toFixed(2));
}
