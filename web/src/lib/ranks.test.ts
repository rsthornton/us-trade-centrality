import { describe, it, expect } from "vitest";
import { divergentStates, hasRank, rankGap } from "./ranks";
import type { BaseCentralityRow } from "../types";

const row = (state: string, gdp: number, rank: number, value: number): BaseCentralityRow => ({
  state_id: 0,
  state,
  betweenness: value,
  eigenvector: value,
  out_degree: value,
  rank_betweenness: rank,
  rank_eigenvector: rank,
  rank_out_degree: rank,
  gdp_billions: 1,
  gdp_rank: gdp,
});

describe("ranks", () => {
  it("treats a zero score as unranked", () => {
    expect(hasRank(row("VT", 51, 21, 0), "betweenness")).toBe(false);
    expect(hasRank(row("KY", 28, 14, 0.1), "betweenness")).toBe(true);
  });
  it("measures the gap as GDP rank minus network rank", () => {
    expect(rankGap(row("KY", 28, 14, 0.1), "eigenvector")).toBe(14);
  });
  it("drops tied-at-zero states from divergence counts", () => {
    const rows = [row("KY", 28, 14, 0.1), row("VT", 51, 21, 0), row("OH", 7, 6, 0.2)];
    expect(divergentStates(rows, "betweenness").map((r) => r.state)).toEqual(["KY"]);
  });
});
