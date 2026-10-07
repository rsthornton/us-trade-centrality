import { useMemo } from "react";
import type { CentralityRow, Measure } from "../types";
import { divergentStates, hasRank, rankGap } from "../lib/ranks";
import { ordinal } from "../lib/format";

const PLAIN: Record<Measure, string> = {
  betweenness: "bridge position",
  eigenvector: "trade prestige",
  out_degree: "export reach",
};

interface HeroFindingProps {
  centralities: CentralityRow[];
  measure: Measure;
}

/** The thesis for the active measure, from the data: how many states diverge
 *  from their GDP rank, and the largest example. States tied at zero are left out. */
export default function HeroFinding({ centralities, measure }: HeroFindingProps) {
  const finding = useMemo(() => {
    const ranked = centralities.filter((r) => hasRank(r, measure));
    if (!ranked.length) return null;
    const lead = ranked.reduce((a, b) => (rankGap(b, measure) > rankGap(a, measure) ? b : a));
    const count = divergentStates(centralities, measure).length;
    const scope =
      ranked.length < centralities.length
        ? `Of the ${ranked.length} states that broker any shortest paths, ${count}`
        : `${count} of ${centralities.length} states`;
    return {
      summary: `${scope} sit 5 or more places away from their GDP rank on ${PLAIN[measure]}.`,
      example: `${lead.state_name} is ${ordinal(lead.gdp_rank)} by GDP and ${ordinal(lead[`rank_${measure}`])} in ${PLAIN[measure]}.`,
    };
  }, [centralities, measure]);

  if (!finding) return null;

  return (
    <span>
      {finding.summary} {finding.example}
    </span>
  );
}
