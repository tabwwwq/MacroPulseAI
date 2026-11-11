import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PulseLine, pulsePath } from "@/components/ui/pulse-line";

describe("pulsePath", () => {
  it("starts on the baseline at the left edge and ends on it at the right edge", () => {
    const d = pulsePath(600, 120, 3);
    expect(d.startsWith("M 0 72")).toBe(true);
    expect(d.endsWith("L 600 72")).toBe(true);
  });

  it("draws one heartbeat (five vertices) per beat, evenly spaced", () => {
    // 1 beat in a 200-wide box: centre x = 100, baseline y = 60 (60 % of 100)
    expect(pulsePath(200, 100, 1)).toBe("M 0 60 L 84 60 L 92 48 L 100 12 L 108 88 L 116 60 L 200 60");
    // every beat adds five "L" vertices; plus the final one
    expect(pulsePath(600, 120, 3).split(" L ").length - 1).toBe(3 * 5 + 1);
  });

  it("returns a flat line when there are no beats", () => {
    expect(pulsePath(100, 50, 0)).toBe("M 0 30 L 100 30");
  });
});

describe("PulseLine", () => {
  it("is decorative: hidden from assistive technology, not focusable", () => {
    const { container } = render(<PulseLine className="h-10" />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).toHaveAttribute("focusable", "false");
    expect(svg).toHaveClass("h-10");
  });

  it("draws a faint static line and an animated trace on the same path", () => {
    const { container } = render(<PulseLine />);
    const base = container.querySelector('path[data-part="base"]');
    const trace = container.querySelector('path[data-part="trace"]');
    expect(base?.getAttribute("d")).toBe(pulsePath(600, 120, 3));
    expect(trace?.getAttribute("d")).toBe(pulsePath(600, 120, 3));
    expect(trace).toHaveClass("animate-trace");
    expect(trace?.getAttribute("stroke-dasharray")).toBe("70 190");
  });
});
