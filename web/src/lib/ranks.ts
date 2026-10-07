import type { BaseCentralityRow, Measure } from "../types";

/** A rank is meaningful only when the score is nonzero. About 30 states have
 *  zero betweenness and share one tied rank, which says nothing about them. */
export function hasRank(row: BaseCentralityRow, measure: Measure): boolean {
  return row[measure] > 0;
}

/** GDP rank minus network rank: positive when the network rank is higher. */
export function rankGap(row: BaseCentralityRow, measure: Measure): number {
  return row.gdp_rank - row[`rank_${measure}`];
}

/** States whose network rank differs from their GDP rank by at least `min` places. */
export function divergentStates(rows: BaseCentralityRow[], measure: Measure, min = 5) {
  return rows.filter((r) => hasRank(r, measure) && Math.abs(rankGap(r, measure)) >= min);
}
