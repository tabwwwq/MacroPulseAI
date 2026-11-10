import { BANDS, formatProbability } from "@/lib/risk";

interface Band {
  upper: number;
  name: string;
}

const R = 80;
const CX = 100;
const CY = 96;

function point(p: number, radius = R): [number, number] {
  const angle = Math.PI * (1 - Math.min(Math.max(p, 0), 1));
  return [CX + radius * Math.cos(angle), CY - radius * Math.sin(angle)];
}

function arc(from: number, to: number): string {
  const [x1, y1] = point(from);
  const [x2, y2] = point(to);
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 0 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
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
  const meta = BANDS[band] ?? { label: band, tone: "neutral", color: "#a0abc0" };
  const segments = bands.map((b, i) => ({
    from: i === 0 ? 0 : Math.min(bands[i - 1]?.upper ?? 0, 1),
    to: Math.min(b.upper, 1),
    name: b.name,
  }));
  const [nx, ny] = point(probability, R - 14);
  const base = baseRate !== null ? point(baseRate, R + 9) : null;
  const baseInner = baseRate !== null ? point(baseRate, R - 9) : null;
  const label = `Estimated probability ${formatProbability(probability)}, ${meta.label.toLowerCase()} band${
    baseRate !== null ? `; training base rate ${formatProbability(baseRate)}` : ""
  }.`;

  return (
    <figure className="flex flex-col items-center">
      <svg viewBox="0 0 200 112" className="w-full max-w-[280px]" role="img" aria-label={label}>
        {segments.map((s) => (
          <path
            key={s.name}
            d={arc(s.from, s.to)}
            fill="none"
            stroke={BANDS[s.name]?.color ?? "#a0abc0"}
            strokeOpacity={s.name === band ? 0.95 : 0.28}
            strokeWidth={14}
          />
        ))}
        {base && baseInner ? (
          <line x1={baseInner[0]} y1={baseInner[1]} x2={base[0]} y2={base[1]} stroke="#e6ebf5" strokeWidth={2} strokeDasharray="2 2" />
        ) : null}
        <line x1={CX} y1={CY} x2={nx} y2={ny} stroke="#e6ebf5" strokeWidth={3} strokeLinecap="round" />
        <circle cx={CX} cy={CY} r={5} fill="#e6ebf5" />
        <text x={18} y={110} fontSize={9} fill="#7f8aa3" textAnchor="middle">0%</text>
        <text x={182} y={110} fontSize={9} fill="#7f8aa3" textAnchor="middle">100%</text>
      </svg>
      <figcaption className="-mt-1 text-center">
        <p className="tabular font-mono text-4xl font-semibold text-fg">{formatProbability(probability)}</p>
        <p className="mt-1 text-sm font-medium" style={{ color: meta.color }}>
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
