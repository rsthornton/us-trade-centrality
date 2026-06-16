import { useState, useMemo } from "react";
import type { BaseCentralityRow, Measure } from "../../types";
import { MEASURES } from "./constants";
import DivergenceDumbbell from "./DivergenceDumbbell";
import DivergenceTable from "./DivergenceTable";

interface RankingsTableProps {
  centralities: BaseCentralityRow[];
  measure: Measure;
  selectedState: string | null;
  onSelectState: (state: string | null) => void;
}

export default function RankingsTable({
  centralities,
  measure,
  selectedState,
  onSelectState,
}: RankingsTableProps) {
  const [expanded, setExpanded] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const measureLabel = MEASURES.find((m) => m.key === measure)?.label ?? measure;

  // Teaser: how many states shift >= 5 rank positions on the active measure.
  const shifted = useMemo(() => {
    const rankKey = `rank_${measure}` as const;
    return centralities.filter((r) => Math.abs(r.gdp_rank - r[rankKey]) >= 5).length;
  }, [centralities, measure]);

  if (!centralities || !centralities.length) return null;

  return (
    <section
      className="mx-6 mt-3 rounded-lg overflow-hidden"
      style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border)" }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between gap-4 px-5 py-3.5 cursor-pointer text-left transition-colors"
        style={{ background: "transparent" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-surface)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <span className="min-w-0">
          <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
            Where GDP and network power diverge
          </span>
          <span className="text-xs ml-2" style={{ color: "var(--text-muted)" }}>
            {shifted} states shift 5+ ranks on {measureLabel.toLowerCase()}
          </span>
        </span>
        <span
          className="text-xs flex items-center gap-1.5 flex-shrink-0"
          style={{ color: "var(--text-secondary)" }}
        >
          {expanded ? "Hide" : "Explore"}
          <span
            className="inline-block transition-transform duration-200"
            style={{ transform: expanded ? "rotate(180deg)" : "none", fontSize: 10 }}
          >
            ▾
          </span>
        </span>
      </button>

      {expanded && (
        <div className="px-5 pb-5" style={{ borderTop: "1px solid var(--border)" }}>
          <p className="text-xs mt-4 mb-3 max-w-2xl leading-relaxed" style={{ color: "var(--text-secondary)" }}>
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
      )}
    </section>
  );
}
