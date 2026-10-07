import { useMemo, useState } from "react";
import type { BaseCentralityRow, Measure } from "../../types";
import { MEASURES } from "./constants";
import { divergentStates, hasRank } from "../../lib/ranks";
import DivergenceDumbbell from "./DivergenceDumbbell";
import DivergenceTable from "./DivergenceTable";

interface DivergenceViewProps {
  centralities: BaseCentralityRow[];
  measure: Measure;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
  /** Active measure color (kept for API stability; the card is neutral). */
  accent?: string;
}

/** The Divergence canvas: a first-class peer to the map (not a bottom drawer). */
export default function DivergenceView({
  centralities,
  measure,
  selectedState,
  onSelectState,
}: DivergenceViewProps) {
  const [showAll, setShowAll] = useState(false);
  const measureLabel = MEASURES.find((m) => m.key === measure)?.label ?? measure;

  const shifted = useMemo(
    () => divergentStates(centralities, measure).length,
    [centralities, measure],
  );
  const ranked = useMemo(
    () => centralities.filter((r) => hasRank(r, measure)).length,
    [centralities, measure],
  );

  if (!centralities.length) return null;

  return (
    <div
      className="p-6"
      style={{
        background: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-card)",
      }}
    >
        <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          GDP rank against {measureLabel.toLowerCase()} rank
        </h2>
        <p className="font-serif text-[19px] font-semibold mt-1" style={{ color: "var(--text-primary)" }}>
          {shifted} of {ranked} states differ from their GDP rank by 5 or more places.
        </p>
        <p className="text-sm mt-2 mb-5 max-w-2xl leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {ranked < centralities.length
            ? `The other ${centralities.length - ranked} states lie on no shortest path between other states, so they have no bridge rank. `
            : ""}
          The chart shows every state with a gap of 5 or more, largest first. Rank 1 is at the left.
        </p>

        <DivergenceDumbbell
          centralities={centralities}
          measure={measure}
          selectedState={selectedState}
          onSelectState={onSelectState}
        />

        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-4 text-xs cursor-pointer flex items-center gap-1.5 transition-opacity hover:opacity-70"
          style={{ color: "var(--accent-blue)" }}
        >
          {showAll ? "Hide the full table" : `Show all ${centralities.length} states as a table`}
        </button>

        {showAll && (
          <DivergenceTable
            centralities={centralities}
            measure={measure}
            selectedState={selectedState}
            onSelectState={onSelectState}
          />
        )}
    </div>
  );
}
