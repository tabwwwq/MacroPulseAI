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
import type { ChartKind, ChartSeries, ChartShading } from "@/components/charts/types";
import { alignSeries } from "@/lib/export";

registerEcharts([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkAreaComponent, CanvasRenderer]);

const theme = {
  darkMode: true,
  backgroundColor: "transparent",
  color: [...chartTheme.palette],
  textStyle: chartTheme.textStyle,
  referenceColor: chartTheme.warn,
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

const valueFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 3 });

/** Display rounding only; the table view and CSV export keep full precision. */
function formatValue(value: number): string {
  return Number.isFinite(value) ? valueFormat.format(value) : "N/A";
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
    getPngDataUrl: () => chart.current?.getDataURL({ type: "png", pixelRatio: 2, backgroundColor: chartTheme.exportBackground }) ?? null,
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
    const plotted: (LineSeriesOption | BarSeriesOption)[] = series.map(({ id, step, color }, index) => {
      const tone = color ?? chartTheme.palette[index % chartTheme.palette.length] ?? chartTheme.accent;
      const shared = {
        id,
        name: columns[index]?.label,
        data: times.map((time, pointIndex) => [time, columns[index]?.values[pointIndex] ?? null]),
      };
      if (kind === "bar") {
        return {
          ...shared,
          type: "bar" as const,
          itemStyle: { color: verticalFade(tone, 1, 0.55), borderRadius: 2 },
          emphasis: { itemStyle: { color: tone } },
        };
      }
      return {
        ...shared,
        type: "line" as const,
        itemStyle: { color: tone },
        lineStyle: glowLine(tone, series.length > 2 ? 1.75 : 2.25),
        // A single series gets a soft fill to the axis; with several, fills would hide each other.
        ...(series.length === 1 ? { areaStyle: { color: verticalFade(tone, 0.28, 0), origin: "start" as const } } : {}),
        // Step series hold each value until the next observation (e.g. a rate decision);
        // they connect across the gaps that alignment with other series introduces.
        connectNulls: Boolean(step),
        smooth: false,
        showSymbol: times.length <= 60, // dense series: line only, values on hover
        symbol: "circle",
        symbolSize: 5,
        emphasis: { scale: 1.6 },
        ...(step ? { step: "end" as const } : {}),
      };
    });
    const sources = [...new Set(series.map((s) => s.source).filter((s): s is string => Boolean(s)))];
    // Separate, explicitly labelled reference series keep shading in the legend and PNG.
    const references: LineSeriesOption[] = shading.map(({ from, to, label, prefix = "External reference" }, index) => ({
      id: `external-reference-${index}`,
      name: `${prefix}: ${label}`,
      type: "line",
      data: [],
      itemStyle: { color: theme.referenceColor },
      markArea: {
        silent: false,
        itemStyle: { color: theme.referenceColor, opacity: 0.14, borderColor: theme.referenceColor, borderWidth: 1, borderType: "dashed" },
        label: { show: false },
        tooltip: { trigger: "item", formatter: () => `${prefix}: ${label}\n${from} – ${to}` },
        data: [[{ name: `${prefix}: ${label}`, xAxis: periodTime(from) }, { xAxis: periodTime(to) }]],
      },
    }));
    const option: ChartOption = {
      animation: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      textStyle: theme.textStyle,
      grid: { left: 16, right: 16, top: 60, bottom: 60, containLabel: true },
      legend: legendStyle,
      tooltip: {
        trigger: "axis",
        renderMode: "richText",
        confine: true,
        ...tooltipStyle,
        axisPointer: axisPointerStyle,
        formatter: (params) => {
          const entries = Array.isArray(params) ? params : [params];
          const firstValue = entries[0]?.value;
          const time = Array.isArray(firstValue) ? Number(firstValue[0]) : NaN;
          const period = labels.get(time) ?? "";
          const values = entries
            .filter((entry) => !String(entry.seriesId ?? "").startsWith("external-reference-"))
            .map((entry) => {
              const value = Array.isArray(entry.value) ? entry.value[1] : null;
              return `${entry.seriesName}: ${value == null ? "N/A" : formatValue(Number(value))}`;
            });
          const referenceLabels = shading
            .filter(({ from, to }) => time >= periodTime(from) && time <= periodTime(to))
            .map(({ label, prefix = "External reference" }) => `${prefix}: ${label}`);
          const sourceLines = sources.length ? [`Source: ${sources.join("; ")}`] : [];
          return [period, ...values, ...referenceLabels, ...sourceLines].join("\n");
        },
      },
      xAxis: { type: "time", ...categoryAxisStyle },
      yAxis: { type: "value", ...valueAxisStyle },
      dataZoom: [
        // The page must keep scrolling over charts: zoom with Ctrl + wheel, pinch, or the slider.
        { type: "inside", filterMode: "none", zoomOnMouseWheel: "ctrl", moveOnMouseWheel: false, preventDefaultMouseMove: false },
        zoomSliderStyle,
      ],
      series: [...plotted, ...references],
    };
    chart.current?.setOption(option, { notMerge: true });
  }, [series, kind, shading]);

  return <div ref={container} role="img" aria-label={ariaLabel} className="w-full min-w-0 tabular" style={{ height }} />;
}
