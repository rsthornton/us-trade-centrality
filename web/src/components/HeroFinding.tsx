import { useMemo } from "react";
import type { CentralityRow, Measure } from "../types";
import { divergentStates, hasRank } from "../lib/ranks";

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
 *  from their GDP rank. States tied at zero are left out. */
export default function HeroFinding({ centralities, measure }: HeroFindingProps) {
  const finding = useMemo(() => {
    const ranked = centralities.filter((r) => hasRank(r, measure));
    if (!ranked.length) return null;
    const count = divergentStates(centralities, measure).length;
    return `${count} of ${ranked.length} states sit 5+ places from their GDP rank in ${PLAIN[measure]}.`;
  }, [centralities, measure]);

  if (!finding) return null;

  return (
    <span>
      {finding}
    </span>
  );
}
