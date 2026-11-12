import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { formatShift, VintageReplayDetails } from "@/components/model/vintage-replay-card";
import { VINTAGE_REPLAY_FIXTURE as data, VINTAGE_REPLAY_UNAVAILABLE as unavailable } from "@/lib/vintage-replay.fixture";

describe("formatShift", () => {
  it("states the change in percentage points and in words", () => {
    expect(formatShift(0.12, 0.315)).toEqual({ text: "+19.5 pp", words: "Higher with the figures as first published" });
    expect(formatShift(0.3, 0.268)).toEqual({ text: "-3.2 pp", words: "Lower with the figures as first published" });
    expect(formatShift(0.2, 0.2004)).toEqual({ text: "0.0 pp", words: "No change" });
    expect(formatShift(0.2, null)).toBeNull();
  });
});

describe("VintageReplayDetails", () => {
  it("shows both estimates, the shift and the band in text", () => {
    render(<VintageReplayDetails data={data} />);
    const today = screen.getByRole("group", { name: "Today's revised data" });
    expect(within(today).getByText("12.0%")).toBeInTheDocument();
    const first = screen.getByRole("group", { name: "As first published" });
    expect(within(first).getByText("31.5%")).toBeInTheDocument();
    expect(within(first).getByText("Moderate")).toBeInTheDocument();
    expect(screen.getByText("+19.5 pp")).toBeInTheDocument();
    expect(screen.getByText("Higher with the figures as first published")).toBeInTheDocument();
  });

  it("compares only the inputs rebuilt from the vintage, and marks revised ones in words", () => {
    render(<VintageReplayDetails data={data} />);
    const table = screen.getByRole("table", { name: "Inputs: today's data versus first published" });
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(8);
    expect(rows.map((r) => within(r).getByRole("rowheader").textContent)).toEqual(
      data.inputs.filter((i) => i.from_vintage).map((i) => i.label),
    );
    const gdp = rows[0]!;
    expect(within(gdp).getByText("-0.52")).toBeInTheDocument();
    expect(within(gdp).getByText("0.71")).toBeInTheDocument();
    expect(within(gdp).getByText("+1.23")).toBeInTheDocument();
    expect(within(gdp).getByText("revised")).toBeInTheDocument();
    const unchanged = rows[1]!;
    expect(within(unchanged).getByText("0.00")).toBeInTheDocument();
    expect(within(unchanged).queryByText("revised")).toBeNull();
    const unemp = rows[6]!;
    expect(within(unemp).getByText("2008-08")).toBeInTheDocument();
    expect(within(unemp).getByText("2008-07")).toBeInTheDocument();
  });

  it("names the inputs that are not revised and the basis of the comparison", () => {
    render(<VintageReplayDetails data={data} />);
    expect(
      screen.getByText("Not revised, identical in both: Policy rate, Policy rate change over 4 quarters, Term spread (10y - 3m)."),
    ).toBeInTheDocument();
    expect(screen.getByText(data.note)).toBeInTheDocument();
    expect(screen.getByText("Fold 2008 · vintage of 2008-09-30 · archive from 1991-12-04")).toBeInTheDocument();
  });

  it("explains why no first-release estimate exists instead of inventing one", () => {
    render(<VintageReplayDetails data={unavailable} />);
    expect(screen.getByText(unavailable.reason as string)).toBeInTheDocument();
    const first = screen.getByRole("group", { name: "As first published" });
    expect(within(first).getByText("N/A")).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.queryByText(/pp$/)).toBeNull();
  });
});
