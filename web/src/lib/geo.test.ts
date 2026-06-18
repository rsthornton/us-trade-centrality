import { describe, it, expect } from "vitest";
import { projectPoint, MAP_WIDTH, MAP_HEIGHT } from "./geo";

describe("projectPoint", () => {
  it("projects a lower-48 point to finite coords inside the viewport", () => {
    const [x, y] = projectPoint(-96, 37.5); // projection center
    expect(Number.isFinite(x)).toBe(true);
    expect(Number.isFinite(y)).toBe(true);
    expect(x).toBeGreaterThan(0);
    expect(x).toBeLessThan(MAP_WIDTH);
    expect(y).toBeGreaterThan(0);
    expect(y).toBeLessThan(MAP_HEIGHT);
  });

  it("routes Alaska (FIPS 02) and Hawaii (FIPS 15) through their insets", () => {
    const lower = projectPoint(-150, 60);
    const ak = projectPoint(-150, 60, "02");
    const hi = projectPoint(-157, 20.5, "15");
    expect(ak).not.toEqual(lower);
    expect(Number.isFinite(hi[0])).toBe(true);
    expect(Number.isFinite(hi[1])).toBe(true);
  });
});
