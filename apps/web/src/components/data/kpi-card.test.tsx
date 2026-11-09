import * as Tooltip from "@radix-ui/react-tooltip";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { KpiCard } from "@/components/data/kpi-card";

describe("KpiCard", () => {
  it("shows an explicit unavailable state instead of a number when there is no value", () => {
    render(<KpiCard label="Inflation" unit="%" note="Source series ends 2025-12." badge={{ label: "Source stale", tone: "warn" }} />);
    expect(screen.getByText("No value available.")).toBeInTheDocument();
    expect(screen.getByText("Source series ends 2025-12.")).toBeInTheDocument();
    expect(screen.getByText("Source stale")).toBeInTheDocument();
    expect(screen.queryByText("%")).not.toBeInTheDocument();
  });

  it("renders a measured value with unit, period and a stale marker", () => {
    render(<KpiCard label="Unemployment" unit="%" value={6.25} period="2026-09" stale />);
    expect(screen.getByText("6.25")).toBeInTheDocument();
    expect(screen.getByText("2026-09")).toBeInTheDocument();
    expect(screen.getByText("Stale")).toBeInTheDocument();
  });

  it("shows the change in words for screen readers, the previous period and the source flag", () => {
    render(
      <KpiCard label="Policy rate" unit="% p.a." value={2.5} period="2026-09-16" change={0.25} changeUnit="pp" previousPeriod="2026-06-17" flag="provisional" />,
    );
    expect(screen.getByText("up")).toHaveClass("sr-only");
    expect(screen.getByText("+0.25 pp")).toBeInTheDocument();
    expect(screen.getByText("vs 2026-06-17")).toBeInTheDocument();
    expect(screen.getByText("provisional")).toBeInTheDocument();
  });

  it("never shows a change without a value", () => {
    render(<KpiCard label="Inflation" unit="%" value={null} change={0.4} changeUnit="pp" />);
    expect(screen.queryByText("+0.40 pp")).not.toBeInTheDocument();
  });

  it("offers provenance through a keyboard-reachable control", () => {
    render(
      <Tooltip.Provider>
        <KpiCard label="Real GDP growth" unit="%" value={0.23} period="2026-Q3" source="Eurostat · namq_10_gdp" provenance={<span>details</span>} />
      </Tooltip.Provider>,
    );
    expect(screen.getByRole("button", { name: "Provenance of Real GDP growth" })).toBeInTheDocument();
  });

  it("marks itself busy while loading", () => {
    const { container } = render(<KpiCard label="GDP" isLoading />);
    expect(container.querySelector("article")).toHaveAttribute("aria-busy", "true");
  });
});
