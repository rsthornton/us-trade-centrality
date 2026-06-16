import { describe, it, expect } from "vitest";
import {
  centralityToColor,
  divergenceToColor,
  interpolateViridis,
  interpolateDivergence,
  MEASURE_COLORS,
} from "./colors";

const HEX = /^#[0-9a-f]{6}$/i;

describe("interpolateViridis", () => {
  it("clamps to the endpoints", () => {
    expect(interpolateViridis(-1)).toBe("#440154");
    expect(interpolateViridis(0)).toBe("#440154");
    expect(interpolateViridis(1)).toBe("#fde725");
    expect(interpolateViridis(2)).toBe("#fde725");
  });
  it("returns a hex color mid-scale", () => {
    expect(interpolateViridis(0.5)).toMatch(HEX);
  });
});

describe("centralityToColor", () => {
  it("returns the mid stop when min === max", () => {
    expect(centralityToColor(5, 5, 5)).toMatch(HEX);
  });
  it("maps min to the low end and max to the high end", () => {
    expect(centralityToColor(0, 0, 1)).toBe("#440154");
    expect(centralityToColor(1, 0, 1)).toBe("#fde725");
  });
});

describe("divergenceToColor", () => {
  it("handles a zero range without dividing by zero", () => {
    expect(divergenceToColor(0, 0)).toMatch(HEX);
  });
  it("maps a zero delta to the divergence midpoint", () => {
    expect(divergenceToColor(0, 10)).toBe(interpolateDivergence(0.5));
  });
});

describe("MEASURE_COLORS", () => {
  it("has a color per measure", () => {
    expect(Object.keys(MEASURE_COLORS).sort()).toEqual([
      "betweenness",
      "eigenvector",
      "out_degree",
    ]);
  });
});
