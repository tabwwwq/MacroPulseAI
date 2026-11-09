import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ChartFrame } from "@/components/charts/chart-frame";
import { TimeSeriesChart, type TimeSeriesChartHandle } from "@/components/charts/time-series-chart";
import type { ChartSeries } from "@/components/charts/types";
import { downloadDataUrl, downloadText, seriesToCsv } from "@/lib/export";

const chartMock = vi.hoisted(() => ({
  init: vi.fn(), setOption: vi.fn(), resize: vi.fn(), dispose: vi.fn(), getDataURL: vi.fn(),
  observe: vi.fn(), disconnect: vi.fn(), addEventListener: vi.fn(), removeEventListener: vi.fn(),
  resizeCallback: undefined as (() => void) | undefined,
}));

vi.mock("echarts/core", () => ({ use: vi.fn(), init: chartMock.init }));
vi.mock("@/lib/export", async (importOriginal) => ({
  ...await importOriginal<typeof import("@/lib/export")>(),
  downloadText: vi.fn(),
  downloadDataUrl: vi.fn(),
}));

// Synthetic test observations only; no fixture is shipped by application components.
const fixture: ChartSeries[] = [
  { id: "test-a", name: "Test A", unit: "%", points: [
    { period: "2026-Q3", value: 3.5 },
    { period: "2026-Q1", value: 0 },
    { period: "2026-Q2", value: null },
  ] },
  { id: "test-b", name: "Test B", unit: "index", points: [{ period: "2026-Q2", value: 102 }] },
];

beforeEach(() => {
  vi.clearAllMocks();
  chartMock.resizeCallback = undefined;
  chartMock.getDataURL.mockReturnValue("data:image/png;base64,dGVzdA==");
  chartMock.init.mockReturnValue({
    setOption: chartMock.setOption, resize: chartMock.resize, dispose: chartMock.dispose, getDataURL: chartMock.getDataURL,
  });
  vi.stubGlobal("ResizeObserver", class {
    constructor(callback: () => void) { chartMock.resizeCallback = callback; }
    observe = chartMock.observe;
    disconnect = chartMock.disconnect;
  });
  vi.stubGlobal("matchMedia", vi.fn(() => ({
    matches: false, addEventListener: chartMock.addEventListener, removeEventListener: chartMock.removeEventListener,
  })));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ChartFrame states", () => {
  it("prioritizes loading over errors and data, without export actions or stale badges", () => {
    render(<ChartFrame title="Test chart" series={fixture} exportName="test" isLoading error={new Error("Test error")} staleSince="2026-01-01T00:00:00Z" />);
    expect(screen.getByRole("status", { name: "Loading Test chart" })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "CSV" })).not.toBeInTheDocument();
    expect(screen.queryByText("Stale")).not.toBeInTheDocument();
    expect(chartMock.init).not.toHaveBeenCalled();
  });

  it("prioritizes error over data and retries through the supplied callback", () => {
    const onRetry = vi.fn();
    render(<ChartFrame title="Test chart" series={fixture} exportName="test" error={new Error("Test error")} onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Request failed");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "CSV" })).not.toBeInTheDocument();
  });

  it.each<{ label: string; series: ChartSeries[] }>([
    { label: "no series", series: [] },
    { label: "all-null observations", series: [{ ...fixture[0]!, points: [{ period: "2026-Q1", value: null }] }] },
  ])(
    "shows an honest empty state with no enabled exports for $label", ({ series }) => {
      render(<ChartFrame title="Test chart" series={series} exportName="test" staleSince="2026-01-01T00:00:00Z" />);
      expect(screen.getByText("No observations yet")).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "CSV" })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "PNG" })).not.toBeInTheDocument();
      expect(screen.queryByText("Stale")).not.toBeInTheDocument();
      expect(chartMock.init).not.toHaveBeenCalled();
    },
  );

  it("supports custom empty copy", () => {
    render(<ChartFrame title="Test chart" series={[]} exportName="test" emptyTitle="Selection unavailable" emptyMessage={<span>No published series.</span>} />);
    expect(screen.getByText("Selection unavailable")).toBeInTheDocument();
    expect(screen.getByText("No published series.")).toBeInTheDocument();
  });

  it("shows the toolbar, aligned table and working exports with their requested filenames", () => {
    render(<ChartFrame title="Test chart" series={fixture} exportName="test-export" allowKindToggle />);
    expect(screen.getByRole("img", { name: "Test chart" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Line" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Bar" }));
    expect(screen.getByRole("button", { name: "Bar" })).toHaveAttribute("aria-pressed", "true");
    expect(chartMock.setOption).toHaveBeenLastCalledWith(expect.objectContaining({
      series: expect.arrayContaining([expect.objectContaining({ id: "test-a", type: "bar" })]),
    }), { notMerge: true });

    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    const table = screen.getByRole("table", { name: "Test chart" });
    expect(screen.getByRole("button", { name: "Table" })).toHaveAttribute("aria-expanded", "true");
    expect(within(table).getByRole("columnheader", { name: "Test A (%)" })).toHaveAttribute("scope", "col");
    expect(within(table).getByRole("columnheader", { name: "Test B (index)" })).toBeInTheDocument();
    expect(within(table).getAllByRole("row").map((row) => [...row.children].map((cell) => cell.textContent))).toEqual([
      ["Period", "Test A (%)", "Test B (index)"],
      ["2026-Q1", "0", "N/A"],
      ["2026-Q2", "N/A", "102"],
      ["2026-Q3", "3.5", "N/A"],
    ]);
    expect(within(table).getByRole("rowheader", { name: "2026-Q1" })).toHaveAttribute("scope", "row");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "CSV" }));
    expect(downloadText).toHaveBeenCalledWith("test-export.csv", seriesToCsv(fixture));
    fireEvent.click(screen.getByRole("button", { name: "PNG" }));
    expect(downloadDataUrl).toHaveBeenCalledWith("test-export.png", "data:image/png;base64,dGVzdA==");
    expect(chartMock.getDataURL).toHaveBeenCalledWith(expect.objectContaining({ type: "png", pixelRatio: 2 }));
    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Test chart" })).toBeInTheDocument();
    expect(chartMock.init).toHaveBeenCalledOnce();
  });

  it("omits the optional kind controls and uses defaultKind", () => {
    render(<ChartFrame title="Test chart" series={fixture} exportName="test" defaultKind="bar" />);
    expect(screen.queryByRole("button", { name: "Line" })).not.toBeInTheDocument();
    expect(chartMock.setOption).toHaveBeenLastCalledWith(expect.objectContaining({
      series: expect.arrayContaining([expect.objectContaining({ id: "test-a", type: "bar" })]),
    }), { notMerge: true });
  });

  it("shows stale and source timestamps in UTC only in the appropriate states", () => {
    const props = { title: "Test chart", series: fixture, exportName: "test" };
    const { rerender } = render(<ChartFrame {...props} />);
    expect(screen.queryByText("Stale")).not.toBeInTheDocument();
    rerender(<ChartFrame {...props} staleSince="2026-11-08T07:02:00+01:00" source={{ label: "Test source", href: "https://example.com/source", retrievedAt: "2026-11-08T07:02:00+01:00" }} />);
    expect(screen.getByText("Stale")).toBeInTheDocument();
    expect(screen.getByText(/Data stale since/)).toHaveTextContent("08 Nov 2026, 06:02 UTC");
    const link = screen.getByRole("link", { name: "Test source" });
    expect(link).toHaveAttribute("href", "https://example.com/source");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(link.parentElement).toHaveTextContent("Source: Test source · retrieved 08 Nov 2026, 06:02 UTC");
    rerender(<ChartFrame {...props} series={[]} staleSince="2026-11-08T07:02:00+01:00" />);
    expect(screen.queryByText("Stale")).not.toBeInTheDocument();
    expect(screen.queryByText(/Data stale since/)).not.toBeInTheDocument();
  });

  it("reports a failed export and clears the failure after a successful retry", () => {
    render(<ChartFrame title="Test chart" series={fixture} exportName="test" />);
    chartMock.getDataURL.mockImplementationOnce(() => { throw new Error("Test canvas failure"); });
    fireEvent.click(screen.getByRole("button", { name: "PNG" }));
    expect(screen.getByRole("alert")).toHaveTextContent("PNG export failed. Please try again.");
    fireEvent.click(screen.getByRole("button", { name: "PNG" }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("TimeSeriesChart lifecycle", () => {
  it("preserves gaps, labels external shading and responds to resize and reduced motion", () => {
    const media = { matches: true, addEventListener: chartMock.addEventListener, removeEventListener: chartMock.removeEventListener };
    vi.stubGlobal("matchMedia", vi.fn(() => media));
    const ref = createRef<TimeSeriesChartHandle>();
    const { unmount } = render(<TimeSeriesChart ref={ref} series={fixture} ariaLabel="Test timeline" shading={[{ from: "2026-02-01", to: "2026-08-01", label: "Test reference" }]} />);
    const time = (month: number) => Date.UTC(2026, month, 1);
    expect(chartMock.setOption).toHaveBeenLastCalledWith(expect.objectContaining({
      animation: false,
      series: expect.arrayContaining([
        expect.objectContaining({ id: "test-a", connectNulls: false, smooth: false, data: [[time(0), 0], [time(3), null], [time(6), 3.5]] }),
        expect.objectContaining({ name: "External reference: Test reference", markArea: expect.objectContaining({
          data: [[{ name: "External reference: Test reference", xAxis: time(1) }, { xAxis: time(7) }]],
        }) }),
      ]),
    }), { notMerge: true });
    act(() => chartMock.resizeCallback?.());
    expect(chartMock.resize).toHaveBeenCalledOnce();
    const motionListener = chartMock.addEventListener.mock.calls[0]?.[1] as (() => void);
    media.matches = false;
    act(() => motionListener());
    expect(chartMock.setOption).toHaveBeenLastCalledWith({ animation: true });
    expect(ref.current?.getPngDataUrl()).toBe("data:image/png;base64,dGVzdA==");
    unmount();
    expect(chartMock.removeEventListener).toHaveBeenCalledWith("change", motionListener);
    expect(chartMock.disconnect).toHaveBeenCalledOnce();
    expect(chartMock.dispose).toHaveBeenCalledOnce();
    expect(ref.current).toBeNull();
  });

  it("updates options when observations change without reinitializing", () => {
    const { rerender } = render(<TimeSeriesChart series={fixture} ariaLabel="Test timeline" />);
    const updated = [{ ...fixture[0]!, points: [{ period: "2026-09", value: 7 }] }];
    rerender(<TimeSeriesChart series={updated} ariaLabel="Test timeline" />);
    expect(chartMock.init).toHaveBeenCalledOnce();
    expect(chartMock.setOption).toHaveBeenLastCalledWith(expect.objectContaining({
      series: [expect.objectContaining({ data: [[Date.UTC(2026, 8, 1), 7]] })],
    }), { notMerge: true });
  });
});
