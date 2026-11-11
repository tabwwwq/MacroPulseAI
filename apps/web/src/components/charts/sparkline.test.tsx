import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Sparkline, sparklineGeometry } from "@/components/charts/sparkline";

describe("sparklineGeometry", () => {
  it("maps the oldest value to the left edge and the newest to the right, highest value on top", () => {
    const g = sparklineGeometry([0, 10, 5], 100, 40, 4);
    expect(g).not.toBeNull();
    expect(g?.points).toEqual([
      [4, 36],
      [50, 4],
      [96, 20],
    ]);
    expect(g?.last).toEqual([96, 20]);
    expect(g?.line).toBe("M 4 36 L 50 4 L 96 20");
    // the area closes the line down to the bottom edge
    expect(g?.area).toBe("M 4 36 L 50 4 L 96 20 L 96 40 L 4 40 Z");
  });

  it("draws a flat series in the vertical middle", () => {
    const g = sparklineGeometry([2, 2, 2], 100, 40, 4);
    expect(g?.points.map(([, y]) => y)).toEqual([20, 20, 20]);
  });

  it("reports the y position of zero only when zero lies strictly inside the value range", () => {
    expect(sparklineGeometry([-10, 10], 100, 40, 4)?.zeroY).toBe(20);
    expect(sparklineGeometry([1, 3], 100, 40, 4)?.zeroY).toBeNull();
    expect(sparklineGeometry([0, 3], 100, 40, 4)?.zeroY).toBeNull();
  });

  it("skips missing values without inventing points and keeps their x slot empty", () => {
    const g = sparklineGeometry([0, null, 10, Number.NaN, 5], 100, 40, 4);
    expect(g?.points).toEqual([
      [4, 36],
      [50, 4],
      [96, 20],
    ]);
    // a gap starts a new sub-path instead of drawing a line across it
    expect(g?.line).toBe("M 4 36 M 50 4 M 96 20");
  });

  it("returns null with fewer than two finite values", () => {
    expect(sparklineGeometry([], 100, 40, 4)).toBeNull();
    expect(sparklineGeometry([3], 100, 40, 4)).toBeNull();
    expect(sparklineGeometry([null, 3, null], 100, 40, 4)).toBeNull();
  });
});

describe("Sparkline", () => {
  it("renders an image with the given accessible name, a line, an area and an end marker", () => {
    const { container } = render(<Sparkline values={[1, 3, 2, 4]} ariaLabel="Inflation, last 4 observations" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("Inflation, last 4 observations");
    expect(container.querySelector('path[data-part="line"]')).not.toBeNull();
    expect(container.querySelector('path[data-part="area"]')).not.toBeNull();
    expect(container.querySelector('[data-part="last"]')).not.toBeNull();
    expect(container.querySelector('line[data-part="zero"]')).toBeNull();
  });

  it("draws a dashed zero line when the series crosses zero", () => {
    const { container } = render(<Sparkline values={[-1, 2]} ariaLabel="Growth" />);
    expect(container.querySelector('line[data-part="zero"]')).not.toBeNull();
  });

  it("renders nothing when there is not enough data", () => {
    const { container } = render(<Sparkline values={[null, 1]} ariaLabel="Growth" />);
    expect(container.firstChild).toBeNull();
  });

  it("uses the tone's design token as stroke colour", () => {
    const { container } = render(<Sparkline values={[1, 2]} ariaLabel="x" tone="warn" />);
    expect(container.querySelector('path[data-part="line"]')?.getAttribute("stroke")).toBe("var(--color-warn)");
  });
});
