import { useId, type JSX } from "react";

export interface SparklineGeometry {
  /** Pixel positions of the finite values only, oldest first. */
  points: [number, number][];
  /** SVG path of the line. */
  line: string;
  /** SVG path of the filled area below the line (closed along the bottom edge). */
  area: string;
  /** Position of the newest finite value. */
  last: [number, number];
  /** y of the value 0 when min < 0 < max, otherwise null. */
  zeroY: number | null;
}

const PAD = 4;

export function sparklineGeometry(
  values: readonly (number | null | undefined)[],
  width: number,
  height: number,
  pad: number,
): SparklineGeometry | null {
  const n = values.length;

  // First pass: collect finite slots and their min/max.
  const finite: { index: number; v: number }[] = [];
  let min = Infinity;
  let max = -Infinity;

  for (let i = 0; i < n; i += 1) {
    const raw = values[i];
    if (typeof raw !== "number" || !Number.isFinite(raw)) continue;
    finite.push({ index: i, v: raw });
    if (raw < min) min = raw;
    if (raw > max) max = raw;
  }

  if (finite.length < 2) return null;

  // Second pass: compute x and y for each finite slot using the full range.
  const pts: { x: number; y: number; index: number }[] = finite.map((f) => {
    const x = n > 1 ? pad + (f.index * (width - 2 * pad)) / (n - 1) : width / 2;
    const y = max === min ? height / 2 : pad + ((max - f.v) / (max - min)) * (height - 2 * pad);
    return { x: round2(x), y: round2(y), index: f.index };
  });

  const points: [number, number][] = pts.map((p) => [p.x, p.y]);
  const lastPt = pts[pts.length - 1];
  const last: [number, number] = [lastPt?.x ?? 0, lastPt?.y ?? 0];

  // Build the line path: "M" for the first point and for every point that
  // follows a gap (i.e. its slot index is not exactly one more than the
  // previous finite point's slot index), "L" otherwise.
  const line = pts
    .map((p, i) => {
      const previous = pts[i - 1];
      const gap = previous === undefined || p.index !== previous.index + 1;
      return `${gap ? "M" : "L"} ${p.x} ${p.y}`;
    })
    .join(" ");

  const firstX = pts[0]?.x ?? 0;
  const area =
    pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") +
    ` L ${last[0]} ${round2(height)} L ${firstX} ${round2(height)} Z`;

  const zeroY = min < 0 && max > 0 ? round2(pad + ((max - 0) / (max - min)) * (height - 2 * pad)) : null;

  return { points, line, area, last, zeroY };
}

function round2(x: number): number {
  return Number(x.toFixed(2));
}

export interface SparklineProps {
  /** Oldest → newest. null / undefined / NaN are gaps and are never interpolated. */
  values: readonly (number | null | undefined)[];
  ariaLabel: string;
  width?: number; // default 120 (viewBox units)
  height?: number; // default 36
  tone?: "accent" | "ok" | "warn" | "danger" | "neutral"; // default "accent"
  className?: string;
}

const TONE_COLOUR: Record<NonNullable<SparklineProps["tone"]>, string> = {
  accent: "var(--color-accent)",
  ok: "var(--color-ok)",
  warn: "var(--color-warn)",
  danger: "var(--color-danger)",
  neutral: "var(--color-fg-muted)",
};

export function Sparkline(props: SparklineProps): JSX.Element | null {
  const { values, ariaLabel, width = 120, height = 36, tone = "accent", className } = props;

  // Hooks must be called unconditionally, before any early return.
  const rawId = useId();
  const gradientId = rawId.replace(/:/g, "");

  const geometry = sparklineGeometry(values, width, height, PAD);
  if (geometry === null) return null;

  const colour = TONE_COLOUR[tone];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel}
      preserveAspectRatio="none"
      className={className}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={colour} stopOpacity={0.35} />
          <stop offset="100%" stopColor={colour} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path data-part="area" d={geometry.area} fill={`url(#${gradientId})`} />
      {geometry.zeroY !== null ? (
        <line
          data-part="zero"
          x1={PAD}
          x2={width - PAD}
          y1={geometry.zeroY}
          y2={geometry.zeroY}
          stroke="var(--color-line-strong)"
          strokeWidth={1}
          strokeDasharray="2 3"
          vectorEffect="non-scaling-stroke"
        />
      ) : null}
      <path
        data-part="line"
        d={geometry.line}
        fill="none"
        stroke={colour}
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      {/* End marker: a zero-length round-capped stroke stays a circle when the SVG is stretched. */}
      <path
        data-part="last"
        d={`M ${geometry.last[0]} ${geometry.last[1]} h 0.01`}
        fill="none"
        stroke={colour}
        strokeWidth={5.5}
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
