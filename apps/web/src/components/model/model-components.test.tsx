import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Contribution } from "@macropulse/shared-types";

import { Contributions } from "@/components/model/contributions";
import { ProbabilityGauge } from "@/components/model/probability-gauge";

const bands = [
  { upper: 0.15, name: "low" },
  { upper: 0.3, name: "moderate" },
  { upper: 0.5, name: "elevated" },
  { upper: 1, name: "high" },
];

describe("ProbabilityGauge", () => {
  it("states probability, band and base rate in text, not only colour", () => {
    render(<ProbabilityGauge probability={0.183} band="moderate" bands={bands} baseRate={0.155} />);
    expect(screen.getByRole("img")).toHaveAccessibleName(
      "Estimated probability 18.3%, moderate band; training base rate 15.5%.",
    );
    expect(screen.getByText("Moderate risk band")).toBeInTheDocument();
    expect(screen.getByText("18.3%")).toBeInTheDocument();
  });
});

describe("Contributions", () => {
  const items: Contribution[] = [
    {
      feature: "term_spread",
      label: "10-year yield minus 3-month rate",
      value: 0.67,
      period: "2026-08",
      contribution: 0.301,
      standardised_value: -0.3,
      training_mean: 1.11,
      outside_training_range: false,
      unusual: false,
    },
    {
      feature: "unemp",
      label: "Unemployment rate",
      value: 14,
      period: "2026-07",
      contribution: -0.08,
      standardised_value: 3.2,
      training_mean: 6.43,
      outside_training_range: true,
      unusual: true,
    },
  ];

  it("shows direction in words, the input value with its period, and range warnings", () => {
    render(<Contributions items={items} unit="log-odds" />);
    expect(screen.getByText(", raises the estimate")).toBeInTheDocument();
    expect(screen.getByText(", lowers the estimate")).toBeInTheDocument();
    expect(screen.getByText(/value 0\.67 · 2026-08 · training mean 1\.11/)).toBeInTheDocument();
    expect(screen.getByText("outside training range")).toBeInTheDocument();
    expect(screen.getByText("+0.301")).toBeInTheDocument();
  });
});
