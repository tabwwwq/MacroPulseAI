"use client";

import { LineChart, type LineSeriesOption } from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
  type DataZoomComponentOption,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from "echarts/components";
import { init, use as registerEcharts, type ComposeOption, type EChartsType } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useImperativeHandle, useRef, type JSX, type Ref } from "react";

import {
  axisPointerStyle,
  categoryAxisStyle,
  chartTheme,
  glowLine,
  legendStyle,
  tooltipStyle,
  valueAxisStyle,
  verticalFade,
  zoomSliderStyle,
} from "@/components/charts/theme";

registerEcharts([LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkLineComponent, CanvasRenderer]);

const theme = {
  backgroundColor: "transparent",
  textStyle: chartTheme.textStyle,
  axisColor: chartTheme.axis,
  actual: chartTheme.accent,
  projection: chartTheme.warn,
  realised: chartTheme.ok,
};

type Option = ComposeOption<LineSeriesOption | GridComponentOption | TooltipComponentOption | LegendComponentOption | DataZoomComponentOption>;

export interface ForecastChartHandle {
  getPngDataUrl(): string | null;
}

export interface ForecastChartProps {
  actuals: { period: string; value: number }[];
  path: { period: string; value: number; lower: number | null; upper: number | null }[];
  realised: { period: string; value: number }[];
  origin: string;
  unit: string;
  modelName: string;
  ariaLabel: string;
  height?: number;
  /** Years of history visible initially (the slider reaches all of it). */
  windowYears?: number;
  ref?: Ref<ForecastChartHandle>;
}

const fmt = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });

function periodTime(period: string): number {
  const quarter = /^(\d{4})-Q([1-4])$/.exec(period);
  if (quarter) return Date.UTC(Number(quarter[1]), (Number(quarter[2]) - 1) * 3, 1);
  return Date.parse(`${period}-01T00:00:00Z`);
}

/**
 * Published history (solid), the selected model's projection (dashed) with its empirical 80 %
 * ribbon, and values published after the origin (green) when the as-of lies in the past. The
 * projection and ribbon start at the last published value so they read as one continuation.
 */
export function ForecastChart({
  actuals, path, realised, origin, unit, modelName, ariaLabel, height = 320, windowYears = 12, ref,
}: ForecastChartProps): JSX.Element {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<EChartsType | null>(null);

  useImperativeHandle(ref, () => ({
    getPngDataUrl: () => chart.current?.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: chartTheme.exportBackground }) ?? null,
  }), []);

  useEffect(() => {
    if (!container.current) return;
    const instance = init(container.current, undefined, { renderer: "canvas" });
    chart.current = instance;
    const observer = new ResizeObserver(() => instance.resize());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      instance.dispose();
      chart.current = null;
    };
  }, []);

  useEffect(() => {
    const last = actuals.at(-1);
    const anchor = last && last.period === origin ? [{ period: last.period, value: last.value, lower: last.value, upper: last.value }] : [];
    const banded = [...anchor, ...path.filter((p) => p.lower !== null && p.upper !== null)];
    const line = [...anchor, ...path];
    const labels = new Map<number, string>();
    for (const p of [...actuals, ...path, ...realised]) labels.set(periodTime(p.period), p.period);
    const bands = new Map(path.map((p) => [periodTime(p.period), p]));
    const end = Math.max(...[...path, ...realised].map((p) => periodTime(p.period)), last ? periodTime(last.period) : 0);
    const start = last ? Date.UTC(new Date(periodTime(last.period)).getUTCFullYear() - windowYears, 0, 1) : undefined;

    const option: Option = {
      animation: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      backgroundColor: theme.backgroundColor,
      textStyle: theme.textStyle,
      grid: { left: 16, right: 20, top: 48, bottom: 60, containLabel: true },
      legend: {
        ...legendStyle,
        data: ["Published", `${modelName} forecast`, "80 % interval", ...(realised.length ? ["Published after origin"] : [])],
      },
      tooltip: {
        trigger: "axis",
        renderMode: "richText",
        confine: true,
        ...tooltipStyle,
        axisPointer: axisPointerStyle,
        formatter: (params) => {
          const entries = Array.isArray(params) ? params : [params];
          const first = entries[0]?.value;
          const time = Array.isArray(first) ? Number(first[0]) : NaN;
          const lines = [labels.get(time) ?? ""];
          for (const e of entries) {
            if (e.seriesId === "band-base" || e.seriesId === "band") continue;
            const v = Array.isArray(e.value) ? e.value[1] : null;
            lines.push(`${e.seriesName}: ${v == null ? "N/A" : `${fmt.format(Number(v))} ${unit}`}`);
          }
          const band = bands.get(time);
          if (band) {
            lines.push(
              band.lower !== null && band.upper !== null
                ? `80 % interval: ${fmt.format(band.lower)} to ${fmt.format(band.upper)}`
                : "80 % interval: N/A (too few past errors)",
            );
          }
          return lines.join("\n");
        },
      },
      xAxis: { type: "time", ...categoryAxisStyle },
      yAxis: { type: "value", scale: true, ...valueAxisStyle },
      dataZoom: [
        { type: "inside", filterMode: "none", zoomOnMouseWheel: "ctrl", moveOnMouseWheel: false, preventDefaultMouseMove: false, startValue: start, endValue: end },
        { ...zoomSliderStyle, startValue: start, endValue: end },
      ],
      series: [
        {
          id: "actual",
          name: "Published",
          type: "line",
          data: actuals.map((a) => [periodTime(a.period), a.value]),
          showSymbol: false,
          lineStyle: glowLine(theme.actual, 2),
          areaStyle: { color: verticalFade(theme.actual, 0.2, 0), origin: "start" },
          itemStyle: { color: theme.actual },
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { color: theme.axisColor, type: "dotted" },
            label: { formatter: `Origin ${origin}`, color: theme.axisColor, position: "insideEndTop" },
            data: [{ xAxis: periodTime(origin) }],
          },
        },
        {
          id: "band-base",
          name: "80 % interval",
          type: "line",
          stack: "band",
          data: banded.map((p) => [periodTime(p.period), p.lower]),
          lineStyle: { opacity: 0 },
          showSymbol: false,
          itemStyle: { color: theme.projection },
          tooltip: { show: false },
        },
        {
          id: "band",
          name: "80 % interval",
          type: "line",
          stack: "band",
          data: banded.map((p) => [periodTime(p.period), (p.upper ?? 0) - (p.lower ?? 0)]),
          lineStyle: { opacity: 0 },
          showSymbol: false,
          areaStyle: { color: verticalFade(theme.projection, 0.3, 0.12) },
          itemStyle: { color: theme.projection },
          tooltip: { show: false },
        },
        {
          id: "projection",
          name: `${modelName} forecast`,
          type: "line",
          data: line.map((p) => [periodTime(p.period), p.value]),
          showSymbol: true,
          symbolSize: 5,
          lineStyle: { ...glowLine(theme.projection, 2.25), type: "dashed" },
          itemStyle: { color: theme.projection },
        },
        ...(realised.length
          ? [
              {
                id: "realised",
                name: "Published after origin",
                type: "line" as const,
                data: realised.map((r) => [periodTime(r.period), r.value]),
                showSymbol: true,
                symbol: "diamond",
                symbolSize: 7,
                lineStyle: glowLine(theme.realised, 1.75),
                itemStyle: { color: theme.realised },
              },
            ]
          : []),
      ],
    };
    chart.current?.setOption(option, { notMerge: true });
  }, [actuals, path, realised, origin, unit, modelName, windowYears]);

  return <div ref={container} role="img" aria-label={ariaLabel} className="w-full min-w-0 tabular" style={{ height }} />;
}
