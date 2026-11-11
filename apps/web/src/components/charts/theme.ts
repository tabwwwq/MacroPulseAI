/**
 * Shared look of every ECharts canvas. Matches the tokens in globals.css — canvas rendering cannot
 * consume Tailwind classes or CSS variables. Charts are transparent so the card surface shows
 * through; PNG exports are flattened onto `exportBackground`.
 */
export const chartTheme = {
  exportBackground: "#131b2c",
  palette: ["#4cc3ff", "#3dd6a3", "#f2667a", "#8f8bff", "#a0abc0"],
  accent: "#4cc3ff",
  ok: "#3dd6a3",
  warn: "#f5b544",
  textStyle: { color: "#a0abc0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" },
  gridLine: "#24304a",
  axis: "#8a95ad",
} as const;

/** `#rrggbb` → `rgba(r, g, b, alpha)`; other colour notations are returned unchanged. */
export function withAlpha(color: string, alpha: number): string {
  const hex = /^#([0-9a-f]{6})$/i.exec(color)?.[1];
  if (!hex) return color;
  const n = Number.parseInt(hex, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

/** Vertical fade from `color` at `from` opacity (top) to `to` (bottom): area fills and bars. */
export function verticalFade(color: string, from: number, to: number) {
  return {
    type: "linear" as const,
    x: 0,
    y: 0,
    x2: 0,
    y2: 1,
    colorStops: [
      { offset: 0, color: withAlpha(color, from) },
      { offset: 1, color: withAlpha(color, to) },
    ],
  };
}

/** Line with a soft glow in its own colour. */
export function glowLine(color: string, width = 2.25) {
  return { color, width, shadowColor: withAlpha(color, 0.55), shadowBlur: 10, shadowOffsetY: 4 };
}

/** Floating tooltip: dark glass panel with a hairline border. */
export const tooltipStyle = {
  backgroundColor: "rgba(16, 24, 43, 0.94)",
  borderColor: "#34425f",
  borderWidth: 1,
  padding: [10, 12] as [number, number],
  textStyle: { ...chartTheme.textStyle, color: "#e7ebf3", fontSize: 12, lineHeight: 18 },
  extraCssText: "border-radius: 12px; box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.9);",
} as const;

/** Crosshair shown with axis tooltips. */
export const axisPointerStyle = {
  type: "line" as const,
  lineStyle: { color: withAlpha(chartTheme.accent, 0.55), width: 1, type: "dashed" as const },
};

export const legendStyle = {
  type: "scroll" as const,
  top: 4,
  icon: "roundRect",
  itemWidth: 14,
  itemHeight: 4,
  itemGap: 18,
  textStyle: chartTheme.textStyle,
  pageIconColor: chartTheme.accent,
  pageTextStyle: chartTheme.textStyle,
} as const;

export const categoryAxisStyle = {
  axisLine: { lineStyle: { color: chartTheme.gridLine } },
  axisTick: { show: false },
  axisLabel: { color: chartTheme.axis, hideOverlap: true },
  splitLine: { show: false },
} as const;

export const valueAxisStyle = {
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: chartTheme.axis },
  splitLine: { lineStyle: { color: chartTheme.gridLine, type: [3, 5] as number[] } },
} as const;

/** Range slider under time charts: a slim track, no miniature of the data. */
export const zoomSliderStyle = {
  type: "slider" as const,
  bottom: 6,
  height: 14,
  borderColor: "transparent",
  backgroundColor: "rgba(11, 16, 32, 0.7)",
  fillerColor: withAlpha(chartTheme.accent, 0.22),
  showDataShadow: false,
  showDetail: false,
  handleSize: "140%",
  handleStyle: { color: "#e7ebf3", borderColor: chartTheme.accent, borderWidth: 1 },
  moveHandleSize: 0,
  brushSelect: false,
  textStyle: chartTheme.textStyle,
};
