import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SupportBadge } from "@/components/data/support-badge";

describe("SupportBadge", () => {
  it.each([
    ["full", "Full support"],
    ["partial", "Partial support"],
    ["unavailable", "No data yet"],
  ] as const)("conveys %s with text, not colour alone", (level, text) => {
    render(<SupportBadge support={{ level, target: "full", reason: "because" }} />);
    const badge = screen.getByText(text);
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("title", "because");
  });

  it("drops the word 'support' in compact mode", () => {
    render(<SupportBadge support={{ level: "partial", target: "full", reason: "r" }} compact />);
    expect(screen.getByText("Partial")).toBeInTheDocument();
  });
});
