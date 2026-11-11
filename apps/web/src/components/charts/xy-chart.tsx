"use client";

import { LineChart, type LineSeriesOption } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from "echarts/components";
import { init, use as registerEcharts, type ComposeOption, type EChartsType } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useRef, type JSX } from "react";

import { chartTheme, glowLine, legendStyle, tooltipStyle, valueAxisStyle } from "@/components/charts/theme";

registerEcharts([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const theme = {
  backgroundColor: "transparent",
  color: [chartTheme.accent, chartTheme.warn, chartTheme.ok, "#f2667a", "#a0abc0"],
  textStyle: chartTheme.textStyle,
  axisColor: chartTheme.axis,
};

type Option = ComposeOption<LineSeriesOption | GridComponentOption | TooltipComponentOption | LegendComponentOption>;

export interface XYSeries {
  name: string;
  points: { x: number; y: number }[];
  dashed?: boolean;
  /** Draw markers only (e.g. calibration bins sized by count). */
  markers?: boolean;
  step?: boolean;
}

export interface XYChartProps {
  series: XYSeries[];
  xLabel: string;
  yLabel: string;
  ariaLabel: string;
  height?: number;
  domain?: [number, number];
}

const fmt = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 3 });

/** Value-axis line chart for ROC, precision-recall and reliability (calibration) curves. */
export function XYChart({ series, xLabel, yLabel, ariaLabel, height = 240, domain = [0, 1] }: XYChartProps): JSX.Element {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<EChartsType | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const instance = init(container.current, theme, { renderer: "canvas" });
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
    const option: Option = {
      animation: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      textStyle: theme.textStyle,
      grid: { left: 12, right: 16, top: 40, bottom: 28, containLabel: true },
      legend: legendStyle,
      tooltip: {
        trigger: "item",
        confine: true,
        ...tooltipStyle,
        formatter: (p) => {
          const item = Array.isArray(p) ? p[0] : p;
          const v = (item?.value ?? []) as number[];
          return `${item?.seriesName ?? ""}\n${xLabel}: ${fmt.format(v[0] ?? NaN)}\n${yLabel}: ${fmt.format(v[1] ?? NaN)}`;
        },
      },
      xAxis: {
        type: "value",
        min: domain[0],
        max: domain[1],
        name: xLabel,
        nameLocation: "middle",
        nameGap: 22,
        ...valueAxisStyle,
      },
      yAxis: {
        type: "value",
        min: domain[0],
        max: domain[1],
        name: yLabel,
        nameLocation: "middle",
        nameGap: 34,
        ...valueAxisStyle,
      },
      series: series.map((s, i) => ({
        name: s.name,
        type: "line" as const,
        data: s.points.map((p) => [p.x, p.y]),
        showSymbol: Boolean(s.markers),
        symbolSize: 8,
        lineStyle: glowLine(theme.color[i % theme.color.length] ?? chartTheme.accent, 2),
        ...(s.markers ? { lineStyle: { width: 1, type: "dotted" as const } } : {}),
        ...(s.dashed ? { lineStyle: { type: "dashed" as const, width: 1 }, itemStyle: { color: theme.axisColor } } : {}),
        ...(s.step ? { step: "end" as const } : {}),
      })),
    };
    chart.current?.setOption(option, { notMerge: true });
  }, [series, xLabel, yLabel, domain]);

  return <div ref={container} role="img" aria-label={ariaLabel} className="w-full min-w-0" style={{ height }} />;
}
