import { describe, it, expect } from "vitest";
import { formatScore, ordinal } from "./format";

describe("ordinal", () => {
  it("handles the teens and the usual suffixes", () => {
    expect([1, 2, 3, 4, 11, 12, 13, 21, 22, 28, 51].map(ordinal)).toEqual([
      "1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "28th", "51st",
    ]);
  });
});

describe("formatScore", () => {
  it("never prints a positive score as zero", () => {
    expect(formatScore(0)).toBe("0");
    expect(formatScore(0.0004)).toBe("<0.001");
    expect(formatScore(0.37219)).toBe("0.372");
  });
});
