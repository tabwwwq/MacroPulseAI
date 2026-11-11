import { describe, expect, it } from "vitest";

import {
  chartTheme,
  glowLine,
  tooltipStyle,
  verticalFade,
  withAlpha,
  zoomSliderStyle,
} from "@/components/charts/theme";

describe("withAlpha", () => {
  it("converts a 6-digit hex colour to rgba with the given alpha", () => {
    expect(withAlpha("#4cc3ff", 0.5)).toBe("rgba(76, 195, 255, 0.5)");
  });

  it("accepts upper-case hex digits", () => {
    expect(withAlpha("#4CC3FF", 0.5)).toBe("rgba(76, 195, 255, 0.5)");
  });

  it("returns non-6-digit-hex colours unchanged", () => {
    expect(withAlpha("rgb(1, 2, 3)", 0.5)).toBe("rgb(1, 2, 3)");
    expect(withAlpha("#fff", 0.5)).toBe("#fff");
    expect(withAlpha("red", 0.5)).toBe("red");
  });
});

describe("verticalFade", () => {
  it("builds a top-to-bottom linear gradient with two colour stops", () => {
    expect(verticalFade("#3dd6a3", 0.3, 0)).toEqual({
      type: "linear",
      x: 0,
      y: 0,
      x2: 0,
      y2: 1,
      colorStops: [
        { offset: 0, color: "rgba(61, 214, 163, 0.3)" },
        { offset: 1, color: "rgba(61, 214, 163, 0)" },
      ],
    });
  });
});

describe("glowLine", () => {
  it("defaults to width 2.25 and keeps the colour", () => {
    const line = glowLine("#4cc3ff");
    expect(line.width).toBe(2.25);
    expect(line.color).toBe("#4cc3ff");
  });

  it("glows in the same colour at 0.55 opacity", () => {
    expect(glowLine("#4cc3ff").shadowColor).toBe("rgba(76, 195, 255, 0.55)");
  });

  it("respects an explicit width", () => {
    expect(glowLine("#4cc3ff", 4).width).toBe(4);
  });
});

describe("chartTheme", () => {
  it("keeps every palette entry a 6-digit hex colour", () => {
    for (const color of chartTheme.palette) {
      expect(color).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });

  it("makes the first palette entry the accent", () => {
    expect(chartTheme.palette[0]).toBe(chartTheme.accent);
  });

  it("uses an opaque 6-digit hex export background", () => {
    expect(chartTheme.exportBackground).toMatch(/^#[0-9a-f]{6}$/i);
  });
});

describe("zoomSliderStyle", () => {
  it("is a slider that does not draw a miniature of the data", () => {
    expect(zoomSliderStyle.type).toBe("slider");
    expect(zoomSliderStyle.showDataShadow).toBe(false);
  });
});

describe("tooltipStyle", () => {
  it("shows light text on a non-transparent background", () => {
    expect(tooltipStyle.textStyle.color).toBe("#e7ebf3");
    expect(tooltipStyle.backgroundColor.endsWith(", 0)")).toBe(false);
  });
});
