"use client";

import { BarChart, LineChart, type BarSeriesOption, type LineSeriesOption } from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TooltipComponent,
  type DataZoomComponentOption,
  type GridComponentOption,
  type LegendComponentOption,
  type TooltipComponentOption,
} from "echarts/components";
import { init, use as registerEcharts, type ComposeOption, type EChartsType } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useImperativeHandle, useRef, type JSX, type Ref } from "react";

import type { ChartKind, ChartSeries, ChartShading } from "@/components/charts/types";
import { alignSeries } from "@/lib/export";

registerEcharts([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkAreaComponent, CanvasRenderer]);

// Matches globals.css. Canvas rendering cannot consume Tailwind classes.
const theme = {
  darkMode: true,
  backgroundColor: "#131b2c",
  color: ["#4cc3ff", "#3dd6a3", "#f2667a", "#2f9bff", "#a0abc0"],
  textStyle: { color: "#a0abc0", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" },
  lineColor: "#24304a",
  axisColor: "#7f8aa3",
  referenceColor: "#f5b544",
};

type ChartOption = ComposeOption<
  LineSeriesOption | BarSeriesOption | GridComponentOption | TooltipComponentOption |
  LegendComponentOption | DataZoomComponentOption
>;

export interface TimeSeriesChartHandle {
  getPngDataUrl(): string | null;
}

export interface TimeSeriesChartProps {
  series: ChartSeries[];
  kind?: ChartKind;
  height?: number;
  shading?: ChartShading[];
  ariaLabel: string;
  ref?: Ref<TimeSeriesChartHandle>;
}

/** Convert period labels to UTC positions, without changing or filling observations. */
function periodTime(period: string): number {
  const quarter = /^(\d{4})-Q([1-4])$/.exec(period);
  if (quarter) return Date.UTC(Number(quarter[1]), (Number(quarter[2]) - 1) * 3, 1);
  return Date.parse(/^\d{4}-\d{2}$/.test(period) ? `${period}-01T00:00:00Z` : period);
}

export function TimeSeriesChart({ series, kind = "line", height = 280, shading = [], ariaLabel, ref }: TimeSeriesChartProps): JSX.Element {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<EChartsType | null>(null);

  useImperativeHandle(ref, () => ({
    getPngDataUrl: () => chart.current?.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: theme.backgroundColor }) ?? null,
  }), []);

  useEffect(() => {
    if (!container.current) return;
    const instance = init(container.current, theme, { renderer: "canvas" });
    chart.current = instance;
    const observer = new ResizeObserver(() => instance.resize());
    observer.observe(container.current);
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updateMotion = () => instance.setOption({ animation: !motion.matches });
    motion.addEventListener("change", updateMotion);
    return () => {
      motion.removeEventListener("change", updateMotion);
      observer.disconnect();
      instance.dispose();
      chart.current = null;
    };
  }, []);

  useEffect(() => {
    const { periods, columns } = alignSeries(series);
    const times = periods.map(periodTime);
    const labels = new Map(times.map((time, index) => [time, periods[index]]));
    const plotted: (LineSeriesOption | BarSeriesOption)[] = series.map(({ id }, index) => ({
      id,
      name: columns[index]?.label,
      type: kind,
      data: times.map((time, pointIndex) => [time, columns[index]?.values[pointIndex] ?? null]),
      ...(kind === "line" ? { connectNulls: false, smooth: false, showSymbol: true, symbolSize: 4 } : {}),
    }));
    // Separate, explicitly labelled reference series keep shading in the legend and PNG.
    const references: LineSeriesOption[] = shading.map(({ from, to, label }, index) => ({
      id: `external-reference-${index}`,
      name: `External reference: ${label}`,
      type: "line",
      data: [],
      itemStyle: { color: theme.referenceColor },
      markArea: {
        silent: false,
        itemStyle: { color: theme.referenceColor, opacity: 0.14, borderColor: theme.referenceColor, borderWidth: 1, borderType: "dashed" },
        label: { show: false },
        tooltip: { trigger: "item", formatter: () => `External reference: ${label}\n${from} – ${to}` },
        data: [[{ name: `External reference: ${label}`, xAxis: periodTime(from) }, { xAxis: periodTime(to) }]],
      },
    }));
    const option: ChartOption = {
      animation: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      textStyle: theme.textStyle,
      grid: { left: 16, right: 16, top: 60, bottom: 60, containLabel: true },
      legend: { type: "scroll", top: 4, textStyle: theme.textStyle },
      tooltip: {
        trigger: "axis",
        renderMode: "richText",
        confine: true,
        backgroundColor: theme.backgroundColor,
        borderColor: theme.lineColor,
        textStyle: theme.textStyle,
        formatter: (params) => {
          const entries = Array.isArray(params) ? params : [params];
          const firstValue = entries[0]?.value;
          const time = Array.isArray(firstValue) ? Number(firstValue[0]) : NaN;
          const period = labels.get(time) ?? "";
          const values = entries.map((entry) => {
            const value = Array.isArray(entry.value) ? entry.value[1] : null;
            return `${entry.seriesName}: ${value == null ? "N/A" : String(value)}`;
          });
          const referenceLabels = shading
            .filter(({ from, to }) => time >= periodTime(from) && time <= periodTime(to))
            .map(({ label }) => `External reference: ${label}`);
          return [period, ...values, ...referenceLabels].join("\n");
        },
      },
      xAxis: { type: "time", axisLine: { lineStyle: { color: theme.axisColor } }, splitLine: { show: false } },
      yAxis: { type: "value", axisLabel: { color: theme.axisColor }, splitLine: { lineStyle: { color: theme.lineColor } } },
      dataZoom: [
        { type: "inside", filterMode: "none" },
        { type: "slider", bottom: 4, height: 20, borderColor: theme.lineColor, textStyle: theme.textStyle },
      ],
      series: [...plotted, ...references],
    };
    chart.current?.setOption(option, { notMerge: true });
  }, [series, kind, shading]);

  return <div ref={container} role="img" aria-label={ariaLabel} className="w-full min-w-0 tabular" style={{ height }} />;
}
