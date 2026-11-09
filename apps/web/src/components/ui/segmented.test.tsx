import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { Segmented } from "@/components/ui/segmented";

function Harness() {
  const [v, setV] = useState<"2" | "4">("2");
  return (
    <>
      <Segmented
        label="Horizon"
        value={v}
        onChange={setV}
        options={[
          { value: "2", label: "2Q" },
          { value: "4", label: "4Q" },
        ]}
      />
      <output>{v}</output>
    </>
  );
}

describe("Segmented", () => {
  it("exposes a labelled radio group and changes on click", () => {
    render(<Harness />);
    expect(screen.getByRole("radiogroup", { name: "Horizon" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: "4Q" }));
    expect(screen.getByRole("radio", { name: "4Q" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("4", { selector: "output" })).toBeInTheDocument();
  });

  it("supports arrow-key navigation with roving tabindex", () => {
    render(<Harness />);
    const group = screen.getByRole("radiogroup");
    fireEvent.keyDown(group, { key: "ArrowRight" });
    expect(screen.getByRole("radio", { name: "4Q" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("radio", { name: "2Q" })).toHaveAttribute("tabindex", "-1");
    fireEvent.keyDown(group, { key: "ArrowRight" }); // wraps around
    expect(screen.getByRole("radio", { name: "2Q" })).toHaveAttribute("aria-checked", "true");
  });
});
