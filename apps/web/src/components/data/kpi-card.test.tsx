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

  it("marks itself busy while loading", () => {
    const { container } = render(<KpiCard label="GDP" isLoading />);
    expect(container.querySelector("article")).toHaveAttribute("aria-busy", "true");
  });
});
