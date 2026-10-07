import { describe, it, expect } from "vitest";
import { quickPickFor } from "./commodity";

describe("quickPickFor", () => {
  it("lights the group that covers a single code", () => {
    expect(quickPickFor("02")).toBe("01-05");
    expect(quickPickFor("17")).toBe("15-19");
    expect(quickPickFor("36")).toBe("35-38");
  });
  it("keeps quick-pick values and leaves other codes unlit", () => {
    expect(quickPickFor("all")).toBe("all");
    expect(quickPickFor("15-19")).toBe("15-19");
    expect(quickPickFor("06")).toBe("");
    expect(quickPickFor("06-09")).toBe("");
  });
});
