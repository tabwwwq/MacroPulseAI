import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RevisionsDetails } from "@/components/data/revisions-card";
import { REVISIONS_FIXTURE as data } from "@/lib/revisions.fixture";

describe("RevisionsDetails", () => {
  it("states the revision statistics in text", () => {
    render(<RevisionsDetails data={data} />);
    expect(screen.getByText("0.70 pp")).toBeInTheDocument();
    expect(screen.getByText("3 first releases")).toBeInTheDocument();
    expect(screen.getByText("Mean |revision| · all")).toBeInTheDocument();
    expect(screen.getByText("1.61 pp")).toBeInTheDocument();
  });

  it("labels each recession signal in words, not colour", () => {
    render(<RevisionsDetails data={data} />);
    const list = screen.getByRole("region", { name: /Technical-recession signals/ });
    expect(within(list).getByText("Revised away")).toBeInTheDocument();
    expect(within(list).getByText("Confirmed by today's data")).toBeInTheDocument();
    expect(within(list).getByText("Only visible in today's data")).toBeInTheDocument();
    expect(within(list).getByText(/first known 2022-07-28: -0.40 \/ -0.23 · today: -0.25 \/ \+0.14/)).toBeInTheDocument();
  });

  it("lists the largest revisions and says how many periods were excluded", () => {
    render(<RevisionsDetails data={data} />);
    const table = screen.getByRole("table", { name: "Largest revisions" });
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows.map((r) => within(r).getByRole("rowheader").textContent)).toEqual(["2020-Q2", "2022-Q2", "2022-Q1"]);
    expect(screen.getByText(/1 earlier or back-filled periods are not first releases/)).toBeInTheDocument();
  });
});
