import { useState, useRef, useEffect } from "react";
import type { BaseCentralityRow, Measure } from "../../types";
import { MEASURES } from "./constants";
import DivergenceScatter from "./DivergenceScatter";
import DivergenceTable from "./DivergenceTable";

const MEASURE_FILLS: Record<Measure, { bg: string; text: string; shadow: string }> = {
  eigenvector: { bg: "#ECFDF5", text: "#065F46", shadow: "rgba(6, 95, 70, 0.12)" },
  betweenness: { bg: "#EFF6FF", text: "#1E40AF", shadow: "rgba(30, 64, 175, 0.12)" },
  out_degree: { bg: "#FFF7ED", text: "#9A3412", shadow: "rgba(154, 52, 18, 0.12)" },
};

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
  const [bounced, setBounced] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (expanded && contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [expanded]);

  useEffect(() => {
    const timer = setTimeout(() => setBounced(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  if (!centralities || !centralities.length) return null;

  const fill = MEASURE_FILLS[measure] || MEASURE_FILLS.eigenvector;

  return (
    <div
      className="mx-6 mt-2 rounded-t-lg overflow-hidden"
      style={{
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderBottom: "none",
      }}
    >
      <div className="flex justify-center py-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="cursor-pointer transition-all duration-200"
          style={{
            background: expanded ? "var(--bg-surface)" : fill.bg,
            color: expanded ? "var(--text-secondary)" : fill.text,
            border: "none",
            borderRadius: 24,
            padding: "10px 24px",
            fontSize: 15,
            fontWeight: 500,
            boxShadow: expanded ? "none" : `0 4px 14px ${fill.shadow}`,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            animation: bounced && !expanded ? "nudge 0.6s ease-in-out 1" : "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = expanded ? "none" : `0 6px 20px ${fill.shadow}`;
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = expanded ? "none" : `0 4px 14px ${fill.shadow}`;
            e.currentTarget.style.transform = "none";
          }}
        >
          <span
            className="inline-block transition-transform duration-200"
            style={{ transform: expanded ? "rotate(180deg)" : "none", fontSize: 11 }}
          >
            ▼
          </span>
          {expanded ? "Collapse" : "See where GDP and network power diverge"}
        </button>
      </div>

      <style>{`
        @keyframes nudge {
          0%, 100% { transform: translateY(0); }
          40% { transform: translateY(6px); }
          70% { transform: translateY(-2px); }
        }
      `}</style>

      {expanded && (
        <div ref={contentRef} className="px-5 pb-5">
          <div className="flex gap-2">
            {MEASURES.map(({ key, label }) => (
              <DivergenceScatter
                key={key}
                centralities={centralities}
                measureKey={key}
                label={label}
                selectedState={selectedState}
                onSelectState={onSelectState}
              />
            ))}
          </div>

          <DivergenceTable
            centralities={centralities}
            measure={measure}
            selectedState={selectedState}
            onSelectState={onSelectState}
          />
        </div>
      )}
    </div>
  );
}
