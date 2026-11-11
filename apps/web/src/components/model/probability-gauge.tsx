import { useId } from "react";

import { BANDS, formatProbability } from "@/lib/risk";

interface Band {
  upper: number;
  name: string;
}

const R = 80;
const CX = 100;
const CY = 100;

function point(p: number, radius = R): [number, number] {
  const angle = Math.PI * (1 - Math.min(Math.max(p, 0), 1));
  return [CX + radius * Math.cos(angle), CY - radius * Math.sin(angle)];
}

function arc(from: number, to: number, radius = R): string {
  const [x1, y1] = point(from, radius);
  const [x2, y2] = point(to, radius);
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${radius} ${radius} 0 0 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}

/**
 * Semicircular probability gauge. The band is also written out in words and the training base
 * rate is marked, so the reading never depends on colour alone.
 */
export function ProbabilityGauge({
  probability,
  band,
  bands,
  baseRate,
}: {
  probability: number;
  band: string;
  bands: Band[];
  baseRate: number | null;
}) {
  const rawId = useId();
  const glowId = `gauge-glow-${rawId.replace(/:/g, "")}`;

  const meta = BANDS[band] ?? { label: band, tone: "neutral", color: "#a0abc0" };
  const segments = bands.map((b, i) => ({
    from: i === 0 ? 0 : Math.min(bands[i - 1]?.upper ?? 0, 1),
    to: Math.min(b.upper, 1),
    name: b.name,
  }));

  const active = segments.find((s) => s.name === band);
  const activeColor = active ? BANDS[active.name]?.color ?? "#a0abc0" : "#a0abc0";

  const [tipX, tipY] = point(probability, R - 16);
  const [hubX, hubY] = point(probability, 0);
  const dx = tipX - hubX;
  const dy = tipY - hubY;
  const len = Math.hypot(dx, dy) || 1;
  const px = -dy / len;
  const py = dx / len;
  const half = 3.5;
  const needlePoints = [
    `${(hubX + px * half).toFixed(2)},${(hubY + py * half).toFixed(2)}`,
    `${tipX.toFixed(2)},${tipY.toFixed(2)}`,
    `${(hubX - px * half).toFixed(2)},${(hubY - py * half).toFixed(2)}`,
  ].join(" ");

  const baseOuter = baseRate !== null ? point(baseRate, R + 9) : null;
  const baseInner = baseRate !== null ? point(baseRate, R - 9) : null;

  const label = `Estimated probability ${formatProbability(probability)}, ${meta.label.toLowerCase()} band${
    baseRate !== null ? `; training base rate ${formatProbability(baseRate)}` : ""
  }.`;

  return (
    <figure className="flex flex-col items-center">
      <svg viewBox="-16 -12 232 134" className="w-full max-w-[320px]" role="img" aria-label={label}>
        <defs>
          <filter id={glowId} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" />
          </filter>
        </defs>

        <path d={arc(0, 1)} fill="none" stroke="#1c2840" strokeWidth={14} strokeLinecap="round" />

        {active ? (
          <path
            d={arc(
              active.from + (active.from === 0 ? 0 : 0.006),
              active.to - (active.to === 1 ? 0 : 0.006),
            )}
            fill="none"
            stroke={activeColor}
            strokeWidth={14}
            strokeOpacity={0.55}
            strokeLinecap="butt"
            filter={`url(#${glowId})`}
            aria-hidden
          />
        ) : null}

        {segments.map((s) => (
          <path
            key={s.name}
            d={arc(
              s.from + (s.from === 0 ? 0 : 0.006),
              s.to - (s.to === 1 ? 0 : 0.006),
            )}
            fill="none"
            stroke={BANDS[s.name]?.color ?? "#a0abc0"}
            strokeOpacity={s.name === band ? 1 : 0.3}
            strokeWidth={10}
            strokeLinecap="butt"
          />
        ))}

        {[0, 0.25, 0.5, 0.75, 1].map((p) => {
          const [x1, y1] = point(p, R + 10);
          const [x2, y2] = point(p, R + 14);
          const end = p === 0 || p === 1;
          const [lx, ly] = end ? [point(p, R)[0], CY + 15] : point(p, R + 22);
          return (
            <g key={p}>
              <line
                x1={x1.toFixed(2)}
                y1={y1.toFixed(2)}
                x2={x2.toFixed(2)}
                y2={y2.toFixed(2)}
                stroke="#34425f"
                strokeWidth={1.5}
              />
              <text
                x={lx.toFixed(2)}
                y={ly.toFixed(2)}
                fontSize={8}
                fill="#8a95ad"
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {Math.round(p * 100)}%
              </text>
            </g>
          );
        })}

        {baseOuter && baseInner ? (
          <line
            x1={baseInner[0].toFixed(2)}
            y1={baseInner[1].toFixed(2)}
            x2={baseOuter[0].toFixed(2)}
            y2={baseOuter[1].toFixed(2)}
            stroke="#e7ebf3"
            strokeWidth={2}
            strokeDasharray="2 2"
          />
        ) : null}

        <polygon
          points={needlePoints}
          fill={activeColor}
          opacity={0.6}
          filter={`url(#${glowId})`}
          aria-hidden
        />
        <polygon points={needlePoints} fill="#e7ebf3" />

        <circle cx={CX} cy={CY} r={7} fill="#131b2c" stroke="#e7ebf3" strokeWidth={2} />
        <circle cx={CX} cy={CY} r={2.5} fill={activeColor} />
      </svg>
      <figcaption className="mt-3 text-center">
        <p className="tabular font-mono text-[44px] font-semibold leading-none tracking-tight text-fg">
          {formatProbability(probability)}
        </p>
        <p className="mt-1 text-sm font-medium" style={{ color: meta.color }}>
          <span
            aria-hidden
            className="mr-2 inline-block size-2 rounded-full align-middle"
            style={{ backgroundColor: meta.color, boxShadow: `0 0 10px ${meta.color}` }}
          />
          {meta.label} risk band
        </p>
        {baseRate !== null ? (
          <p className="mt-1 text-xs text-fg-subtle">
            Dashed tick: base rate in the training sample, {formatProbability(baseRate)}
          </p>
        ) : null}
      </figcaption>
    </figure>
  );
}
