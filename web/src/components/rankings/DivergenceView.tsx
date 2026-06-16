import { useMemo, useState } from "react";
import type { BaseCentralityRow, Measure } from "../../types";
import { MEASURES } from "./constants";
import DivergenceDumbbell from "./DivergenceDumbbell";
import DivergenceTable from "./DivergenceTable";

interface DivergenceViewProps {
  centralities: BaseCentralityRow[];
  measure: Measure;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
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

  const shifted = useMemo(() => {
    const rankKey = `rank_${measure}` as const;
    return centralities.filter((r) => Math.abs(r.gdp_rank - r[rankKey]) >= 5).length;
  }, [centralities, measure]);

  if (!centralities.length) return null;

  return (
    <div className="px-6">
      <div
        className="p-6"
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-card)",
        }}
      >
        <div className="flex items-baseline justify-between gap-4 flex-wrap mb-1">
          <h2 className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>
            Where GDP and network power diverge
          </h2>
          <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
            {shifted} states shift 5+ ranks on {measureLabel.toLowerCase()}
          </span>
        </div>
        <p className="text-sm mb-5 max-w-2xl leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          Each state's economic size (GDP rank) compared to its position in the trade network
          ({measureLabel.toLowerCase()} rank). The longer the bar, the more its structural power
          diverges from what GDP would predict.
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
          {showAll ? "Hide full ranking" : "Show all 51 states"}
          <span
            className="inline-block transition-transform duration-200"
            style={{ transform: showAll ? "rotate(180deg)" : "none", fontSize: 9 }}
          >
            ▾
          </span>
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
    </div>
  );
}
